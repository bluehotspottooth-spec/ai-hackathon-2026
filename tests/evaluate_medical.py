"""
evaluate_medical.py: the MEDICAL TEST (part C3 of our brief).
Does our medical layer (GP rules + glossary) translate medical sentences better than plain Gemini?

WHAT IT TESTS
  93 English sentences said by doctors and patients in the 17 PriMock57 consultations we KEPT ASIDE
  (tests/test_set_medical.csv; never used to build anything). Each sentence contains at least one
  term from our medical glossary. Every sentence is translated from English into each of our
  11 patient languages TWICE, with the same AI model and settings:
    - BASELINE:    plain Gemini, "translate this into <language>"
    - VOICEBRIDGE: the same model + our GP interpreter rules + our medical glossary (backend/prompts.py)
  Text in, text out: this isolates the TRANSLATION step (speech recognition is not part of this test).

HOW EACH PAIR IS SCORED
  1. Blind AI judge (main score). A different Gemini model sees the English sentence and the two
     translations in RANDOM order labelled A and B (it is never told which is ours). For each it
     says whether the medical term(s) are translated correctly, gives an accuracy score 1-5, notes
     any errors, and picks the better one (or a tie).
  2. Numbers kept: every number in the English sentence (e.g. 500, 3) must appear in the translation.
  3. Glossary match: does the translation use our glossary's word for the term? (Only a consistency
     check: VoiceBridge is GIVEN the glossary, so it is expected to score higher here.)

HONEST LIMITS: the judge is an AI, not a native speaker; native speakers should check a sample.
Our glossary translations are AI-drafted and not yet verified. Only English -> patient language is
tested here (PriMock57 is in English); patient-language -> English needs recordings from real speakers.

RUN (from the voicebridge folder; uses the Gemini key in .env, no ElevenLabs credits):
    .venv\\Scripts\\python -X utf8 tests\\evaluate_medical.py                 # all 11 languages
    .venv\\Scripts\\python -X utf8 tests\\evaluate_medical.py --langs ur,ar --limit 5   # quick trial
It saves progress as it goes (tests/results/medical/raw_results.jsonl), so if it stops you can
simply run it again and it continues where it left off. Then it writes the result files.
"""

import argparse
import csv
import json
import random
import re
import sys
import threading
import time
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend import pipeline, prompts  # noqa: E402

TEST_SET = ROOT / "tests" / "test_set_medical.csv"
OUT = ROOT / "tests" / "results" / "medical"
RAW = OUT / "raw_results.jsonl"

PATIENT_LANGS = ["pl", "ro", "pa", "ur", "pt", "es", "ar", "bn", "gu", "it", "fa"]  # census order
TRANSLATE_MODEL = pipeline.MODEL            # the model the live app uses (gemini-3.5-flash-lite)
JUDGE_MODEL = "gemini-4-hydrogen"           # a DIFFERENT, stronger model judges, so it is not marking its own work
# (Note: gemini-4-hydrogen also drafted our glossary translations in build_glossary.py, so it may
#  slightly favour glossary words. We report this as a limitation.)
SEED = 2026                                 # same seed as our data split: A/B order is reproducible
WORKERS = 10                                # how many sentences are processed at the same time


# ----------------------------------------------------------------------------- AI calls
class Translation(BaseModel):
    translation: str


class OneVerdict(BaseModel):
    term_correct: bool = Field(description="Every key medical term is translated correctly and naturally (a correct synonym counts).")
    accuracy: int = Field(description="1-5. 5 = complete, exact meaning (including negations, numbers, doses, body parts). 3 = understandable but something is lost or changed. 1 = wrong or dangerous.")
    errors: str = Field(description="Short English note of any meaning error, omission or addition. Empty if none.")


class Verdict(BaseModel):
    a: OneVerdict
    b: OneVerdict
    better: Literal["A", "B", "tie"]


def _call(model: str, text: str, schema: type[BaseModel], system: str | None = None, minimal_thinking=False):
    """One Gemini call with JSON output; retries with growing waits (rate limits, busy server)."""
    request = {
        "model": model,
        "input": text,
        "response_format": {"type": "text", "mime_type": "application/json", "schema": schema.model_json_schema()},
    }
    if system:
        request["system_instruction"] = system
    if minimal_thinking:
        request["generation_config"] = {"thinking_level": "minimal"}
    for attempt in range(5):
        try:
            r = pipeline._client.interactions.create(**request, timeout=60)
            return schema.model_validate_json(r.output_text)
        except Exception as e:
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1) + random.random())


def translate(text: str, lang: str, speaker: str, medical: bool) -> str:
    name = prompts.LANGUAGES[lang]
    if not medical:   # BASELINE: no rules, no glossary
        return _call(TRANSLATE_MODEL, f"Translate the following English text into {name}:\n\n{text}",
                     Translation, minimal_thinking=True).translation.strip()
    # VOICEBRIDGE: the app's own interpreter rules + script rule + glossary, as text instead of audio
    who = "doctor" if speaker == "doctor" else "patient"
    request = (f'The {who} said, in English: "{text}"\n'
               f"Translate it into {name} following your interpreter rules. "
               + prompts._script_rule("en", lang) + prompts._glossary_block(lang))
    return _call(TRANSLATE_MODEL, request, Translation, system=prompts.medical_system_instruction(),
                 minimal_thinking=True).translation.strip()


def judge(text: str, terms: str, lang: str, a: str, b: str) -> Verdict:
    name = prompts.LANGUAGES[lang]
    prompt = (f"You are an expert medical interpreter, fluent in English and {name}.\n"
              f"An English sentence from a UK GP consultation was translated into {name} by two systems.\n\n"
              f'English: "{text}"\nKey medical term(s): {terms}\n\n'
              f"Translation A: {a}\n\nTranslation B: {b}\n\n"
              "Judge each translation for a patient who only understands this language. Check the key "
              "medical terms, negations, numbers, doses, body parts, and anything added or left out. "
              "Ignore small differences of style. Then say which is better overall, or 'tie'.")
    return _call(JUDGE_MODEL, prompt, Verdict)


# ----------------------------------------------------------------------------- simple checks
def _norm(s: str) -> str:
    """Lower case, no accents/vowel marks, any script's digits -> 0-9 (so ٥٠٠ == 500)."""
    s = "".join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in s)
    s = unicodedata.normalize("NFKD", s.lower().replace("‌", ""))
    return "".join(c for c in s if not unicodedata.combining(c))


def numbers_kept(source: str, translation: str) -> bool | None:
    nums = re.findall(r"\d+(?:\.\d+)?", source)
    if not nums:
        return None                                   # nothing to check
    out = _norm(translation)
    return all(n in out for n in nums)


def glossary_match(terms: list[str], lang: str, translation: str, glossary: dict) -> bool | None:
    """Approximate: each word of the glossary translation (minus its last 2 letters, to allow for
    grammar endings like Polish gorączka/gorączkę) must appear in the translation."""
    checks = []
    out = _norm(translation)
    for t in terms:
        g = glossary.get(t.lower(), {}).get("translations", {}).get(lang, "")
        if not g:
            continue
        words = [w for w in re.split(r"[\s/,;]+", _norm(g)) if w]
        checks.append(all(w[:max(3, len(w) - 2)] in out for w in words))
    return all(checks) if checks else None


# ----------------------------------------------------------------------------- run
def run_one(row: dict, lang: str, glossary: dict) -> dict:
    terms = [t.strip() for t in row["glossary_terms"].split(";") if t.strip()]
    t0 = time.perf_counter()
    base = translate(row["text_en"], lang, row["speaker"], medical=False)
    vb = translate(row["text_en"], lang, row["speaker"], medical=True)
    # Blind order: the seed decides per sentence+language whether ours is A or B
    ours_is_a = random.Random(f"{SEED}-{row['id']}-{lang}").random() < 0.5
    a, b = (vb, base) if ours_is_a else (base, vb)
    v = judge(row["text_en"], ", ".join(terms), lang, a, b)
    ours, theirs = (v.a, v.b) if ours_is_a else (v.b, v.a)
    winner = {"tie": "tie", "A": "voicebridge" if ours_is_a else "baseline",
              "B": "baseline" if ours_is_a else "voicebridge"}[v.better]
    return {
        "id": row["id"], "lang": lang, "speaker": row["speaker"], "consultation": row["consultation_id"],
        "english": row["text_en"], "terms": "; ".join(terms),
        "baseline": base, "voicebridge": vb,
        "base_term_ok": theirs.term_correct, "vb_term_ok": ours.term_correct,
        "base_accuracy": theirs.accuracy, "vb_accuracy": ours.accuracy,
        "base_errors": theirs.errors, "vb_errors": ours.errors,
        "judge_prefers": winner, "voicebridge_was": "A" if ours_is_a else "B",
        "base_numbers_ok": numbers_kept(row["text_en"], base), "vb_numbers_ok": numbers_kept(row["text_en"], vb),
        "base_glossary_match": glossary_match(terms, lang, base, glossary),
        "vb_glossary_match": glossary_match(terms, lang, vb, glossary),
        "seconds": round(time.perf_counter() - t0, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default=",".join(PATIENT_LANGS))
    ap.add_argument("--limit", type=int, default=0, help="only the first N sentences (for a quick trial)")
    args = ap.parse_args()
    langs = [l.strip() for l in args.langs.split(",") if l.strip()]

    rows = list(csv.DictReader(TEST_SET.open(encoding="utf-8")))
    if args.limit:
        rows = rows[:args.limit]
    glossary = {e["term"].lower(): e for e in prompts.load_glossary()}

    OUT.mkdir(parents=True, exist_ok=True)
    done = {(r["id"], r["lang"]) for r in _load_raw()}
    jobs = [(r, l) for l in langs for r in rows if (r["id"], l) not in done]
    print(f"{len(rows)} sentences x {len(langs)} languages: {len(done)} already done, {len(jobs)} to do. "
          f"Translator: {TRANSLATE_MODEL}, judge: {JUDGE_MODEL}")

    lock, failed, n = threading.Lock(), 0, 0
    with ThreadPoolExecutor(WORKERS) as pool, RAW.open("a", encoding="utf-8") as f:
        futures = {pool.submit(run_one, r, l, glossary): (r["id"], l) for r, l in jobs}
        for fut in as_completed(futures):
            n += 1
            try:
                res = fut.result()
                with lock:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n"); f.flush()
            except Exception as e:
                failed += 1
                print(f"  failed {futures[fut]}: {type(e).__name__}: {str(e)[:120]}")
            if n % 50 == 0 or n == len(jobs):
                print(f"  {n}/{len(jobs)} done ({failed} failed)")
    if failed:
        print(f"{failed} pairs failed: run the script again to retry just those.")
    write_reports(rows, langs)


def _load_raw() -> list[dict]:
    if not RAW.exists():
        return []
    return [json.loads(l) for l in RAW.read_text(encoding="utf-8").splitlines() if l.strip()]


# ----------------------------------------------------------------------------- reports
def _pct(xs):
    xs = [x for x in xs if x is not None]
    return round(100 * sum(xs) / len(xs)) if xs else None


def _avg(xs):
    return round(sum(xs) / len(xs), 2) if xs else None


def write_reports(rows, langs):
    ids = {r["id"] for r in rows}
    res = [r for r in _load_raw() if r["id"] in ids and r["lang"] in langs]
    by_lang = defaultdict(list)
    for r in res:
        by_lang[r["lang"]].append(r)

    summary = []
    for lang in langs + ["ALL"]:
        rs = res if lang == "ALL" else by_lang.get(lang, [])
        if not rs:
            continue
        summary.append({
            "language": "ALL LANGUAGES" if lang == "ALL" else f"{prompts.LANGUAGES[lang]} ({lang})",
            "sentences": len(rs),
            "term_correct_baseline_%": _pct([r["base_term_ok"] for r in rs]),
            "term_correct_voicebridge_%": _pct([r["vb_term_ok"] for r in rs]),
            "accuracy_baseline_1to5": _avg([r["base_accuracy"] for r in rs]),
            "accuracy_voicebridge_1to5": _avg([r["vb_accuracy"] for r in rs]),
            "judge_prefers_voicebridge_%": _pct([r["judge_prefers"] == "voicebridge" for r in rs]),
            "judge_prefers_baseline_%": _pct([r["judge_prefers"] == "baseline" for r in rs]),
            "tie_%": _pct([r["judge_prefers"] == "tie" for r in rs]),
            "numbers_kept_baseline_%": _pct([r["base_numbers_ok"] for r in rs]),
            "numbers_kept_voicebridge_%": _pct([r["vb_numbers_ok"] for r in rs]),
            "glossary_match_baseline_%": _pct([r["base_glossary_match"] for r in rs]),
            "glossary_match_voicebridge_%": _pct([r["vb_glossary_match"] for r in rs]),
        })
    with (OUT / "results_by_language.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)

    cols = ["id", "lang", "speaker", "consultation", "english", "terms", "baseline", "voicebridge",
            "base_term_ok", "vb_term_ok", "base_accuracy", "vb_accuracy", "judge_prefers",
            "base_errors", "vb_errors", "base_numbers_ok", "vb_numbers_ok",
            "base_glossary_match", "vb_glossary_match", "voicebridge_was"]
    res.sort(key=lambda r: (langs.index(r["lang"]), r["id"]))
    with (OUT / "all_translations.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(res)

    _write_examples(res)
    print(f"Wrote {OUT / 'results_by_language.csv'}, all_translations.csv and examples.md")
    for s in summary:
        print(f"  {s['language']:<22} term correct {s['term_correct_baseline_%']}% -> {s['term_correct_voicebridge_%']}% | "
              f"accuracy {s['accuracy_baseline_1to5']} -> {s['accuracy_voicebridge_1to5']} | "
              f"judge prefers VB {s['judge_prefers_voicebridge_%']}% / baseline {s['judge_prefers_baseline_%']}%")


def _write_examples(res):
    """Side-by-side examples: where VoiceBridge won, where it LOST, and where both got it wrong."""
    rng = random.Random(SEED)
    win = [r for r in res if r["judge_prefers"] == "voicebridge" and r["vb_term_ok"] and not r["base_term_ok"]]
    lose = [r for r in res if r["judge_prefers"] == "baseline" and r["vb_accuracy"] < r["base_accuracy"]]
    both = [r for r in res if not r["vb_term_ok"] and not r["base_term_ok"]]
    parts = ["# Medical test: side-by-side examples\n",
             "Picked at random (seed 2026) from `all_translations.csv`. Scores and notes come from the blind AI judge, "
             "**not** a native speaker, so treat them as a first check. Every row is in `all_translations.csv`.\n"]
    for title, group, note in [
        ("Where VoiceBridge did better", win, "Judge: VoiceBridge translated the medical term correctly, the baseline did not."),
        ("Where VoiceBridge did WORSE (failures)", lose, "Judge preferred the plain baseline and scored VoiceBridge lower."),
        ("Where BOTH got the medical term wrong", both, "Neither system translated the key term correctly."),
    ]:
        parts.append(f"\n## {title} ({len(group)} cases)\n\n{note}\n")
        for r in rng.sample(group, min(6, len(group))):
            parts.append(
                f"\n**{r['id']} · {prompts.LANGUAGES[r['lang']]} · {r['speaker']}** · term: *{r['terms']}*\n\n"
                f"| | Text | Term OK | Accuracy (1-5) | Judge's note |\n|---|---|---|---|---|\n"
                f"| English | {r['english']} | | | |\n"
                f"| Baseline | {r['baseline']} | {'✅' if r['base_term_ok'] else '❌'} | {r['base_accuracy']} | {r['base_errors'] or '-'} |\n"
                f"| VoiceBridge | {r['voicebridge']} | {'✅' if r['vb_term_ok'] else '❌'} | {r['vb_accuracy']} | {r['vb_errors'] or '-'} |\n")
    (OUT / "examples.md").write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    main()
