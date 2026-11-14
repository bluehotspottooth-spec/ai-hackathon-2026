"""
build_glossary.py: builds VoiceBridge's medical glossary (step C1).

Run from the project folder, one step at a time:
  python -X utf8 tests/build_glossary.py split     # 1. split PriMock57 into 40 BUILD / 17 TEST
  python -X utf8 tests/build_glossary.py extract   # 2. Gemini lists medical terms in the 40 BUILD consultations
  python -X utf8 tests/build_glossary.py build     # 3. choose ~80-100 terms + draft translations -> backend/glossary.json

The rules (see docs/DATASET_CHECKING_PLAN.md):
  - Terms come ONLY from the 40 BUILD consultations. The 17 TEST ones are for testing.
  - Translations are drafted by AI and marked verified=false until a native speaker checks them.
  - SNOMED CT IDs are left empty: a person looks each one up on termbrowser.nhs.uk.
"""

import csv
import json
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import primock57  # noqa: E402
from backend.pipeline import _client  # noqa: E402  (same Gemini connection the app uses)
from backend.prompts import LANGUAGES, SCRIPTS  # noqa: E402

SPLIT_FILE = ROOT / "data" / "split.json"
RAW_TERMS = ROOT / "data" / "primock57_terms_raw.json"
COUNTS_CSV = ROOT / "data" / "term_counts.csv"
GLOSSARY = ROOT / "backend" / "glossary.json"

SEED = 2026            # fixed seed: anyone re-running the split gets the same 40/17
N_BUILD = 40
EXTRACT_MODEL = "gemini-3.5-flash-lite"   # fast; just listing terms
TRANSLATE_MODEL = "gemini-4-hydrogen"     # slower but stronger: quality matters more than speed here
MAX_FREQUENT = 50

# NHS "call 999 / go to A&E" style warning signs. Always in the glossary, marked urgent.
URGENT_TERMS = [
    "chest pain", "chest tightness", "shortness of breath", "difficulty breathing",
    "coughing up blood", "vomiting blood", "black stools", "severe bleeding",
    "face drooping", "arm weakness", "slurred speech", "sudden severe headache",
    "fainting", "loss of consciousness", "seizure", "stiff neck",
    "rash that does not fade when pressed", "confusion", "swollen lips or tongue",
    "suicidal thoughts", "self-harm", "severe abdominal pain", "bleeding in pregnancy",
]

# Medicines commonly prescribed by UK GPs. Always included.
UK_GP_MEDICINES = [
    "paracetamol", "ibuprofen", "codeine", "amoxicillin", "antibiotic", "omeprazole",
    "salbutamol inhaler", "metformin", "insulin", "amlodipine", "ramipril", "atorvastatin",
    "aspirin", "sertraline", "levothyroxine",
]


# ------------------------------------------------------------------ 1. split
def split():
    ids = primock57.consultation_ids()
    rng = random.Random(SEED)
    shuffled = ids[:]
    rng.shuffle(shuffled)
    result = {
        "seed": SEED,
        "note": "BUILD = used to make the glossary. TEST = only for the final medical test (C3). Never use TEST to build.",
        "build": sorted(shuffled[:N_BUILD]),
        "test": sorted(shuffled[N_BUILD:]),
    }
    SPLIT_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{len(ids)} consultations -> {len(result['build'])} BUILD, {len(result['test'])} TEST. Saved {SPLIT_FILE}")


# ------------------------------------------------------------------ 2. extract
class Term(BaseModel):
    term: str
    category: Literal["symptom", "condition", "medicine", "test_or_procedure", "body_part", "other"]


class TermList(BaseModel):
    terms: list[Term]


EXTRACT_PROMPT = """Below is a transcript of a UK GP consultation.
List every MEDICAL term that is mentioned: symptoms, conditions/diagnoses, medicines, tests or procedures, and clinically important body parts.
- Write each term in standard UK English as a GP would write it (e.g. "diarrhoea", "shortness of breath"), lowercase, singular.
- Merge different wordings of the same thing into one term.
- Leave out generic words that are not medical terms (e.g. "doctor", "appointment", "pain" on its own, "medication" on its own).

Transcript:
"""


def _extract_one(cid: str) -> tuple[str, list[dict]]:
    r = _client.interactions.create(
        model=EXTRACT_MODEL,
        input=EXTRACT_PROMPT + primock57.as_text(cid),
        response_format={"type": "text", "mime_type": "application/json", "schema": TermList.model_json_schema()},
        generation_config={"thinking_level": "minimal"},
        timeout=60,
    )
    terms = TermList.model_validate_json(r.output_text).terms
    return cid, [t.model_dump() for t in terms]


def extract():
    build_ids = json.loads(SPLIT_FILE.read_text())["build"]
    raw = json.loads(RAW_TERMS.read_text(encoding="utf-8")) if RAW_TERMS.exists() else {}
    todo = [c for c in build_ids if c not in raw]  # resume if a previous run stopped
    print(f"Extracting terms from {len(todo)} BUILD consultations ({len(raw)} already done)...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        for cid, terms in pool.map(_extract_one, todo):
            raw[cid] = terms
            print(f"  {cid}: {len(terms)} terms", flush=True)
            RAW_TERMS.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    # Count in how many consultations each term appears (not how many times).
    counts, category = Counter(), {}
    for cid in build_ids:
        seen = {t["term"].strip().lower() for t in raw[cid]}
        counts.update(seen)
        for t in raw[cid]:
            category.setdefault(t["term"].strip().lower(), t["category"])
    with COUNTS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["term", "category", "consultations"])
        for term, n in counts.most_common():
            w.writerow([term, category[term], n])
    print(f"{len(counts)} different terms. Saved {COUNTS_CSV}")


# ------------------------------------------------------------------ 3. build
class TermTranslations(BaseModel):
    term: str
    translations: dict[str, str]


class TranslationBatch(BaseModel):
    items: list[TermTranslations]


def _translate_batch(terms: list[str]) -> dict[str, dict[str, str]]:
    langs = [l for l in LANGUAGES if l != "en"]
    lang_rules = "\n".join(f"- {l}: {LANGUAGES[l]}, written in {SCRIPTS[l]}" for l in langs)
    prompt = (
        "You are helping build a glossary for medical interpreters in UK GP appointments.\n"
        "Translate each English term into every language below. Use the words a patient with no medical "
        "training would understand and that a professional interpreter would say aloud. No slashes or "
        "alternatives: give one translation per language.\n"
        f"Languages (use these codes as keys):\n{lang_rules}\n\nTerms:\n" + "\n".join(f"- {t}" for t in terms)
    )
    r = _client.interactions.create(
        model=TRANSLATE_MODEL,
        input=prompt,
        response_format={"type": "text", "mime_type": "application/json", "schema": TranslationBatch.model_json_schema()},
        generation_config={"thinking_level": "low"},
        timeout=600,
    )
    return {i.term.strip().lower(): i.translations for i in TranslationBatch.model_validate_json(r.output_text).items}


def build():
    with COUNTS_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    freq = {r["term"]: int(r["consultations"]) for r in rows}

    chosen: dict[str, dict] = {}

    def add(term: str, category: str, source: str):
        key = term.strip().lower()
        entry = chosen.setdefault(key, {"term": key, "category": category, "sources": []})
        if source not in entry["sources"]:
            entry["sources"].append(source)

    # a) most frequent clinical terms in the BUILD consultations (in at least 2 of them)
    clinical = [r for r in rows if r["category"] in ("symptom", "condition", "test_or_procedure") and int(r["consultations"]) >= 2]
    for r in clinical[:MAX_FREQUENT]:
        add(r["term"], "frequent", "PriMock57 BUILD set (frequency)")
    # b) medicines: mentioned in the BUILD set + common UK GP medicines
    for r in rows:
        if r["category"] == "medicine" and int(r["consultations"]) >= 2:
            add(r["term"], "medicine", "PriMock57 BUILD set (frequency)")
    for m in UK_GP_MEDICINES:
        add(m, "medicine", "Common UK GP medicines")
    # c) urgent warning signs (always included; override the category)
    for u in URGENT_TERMS:
        add(u, "urgent", "NHS urgent warning signs")
        chosen[u]["category"] = "urgent"

    terms = list(chosen)
    print(f"Chosen {len(terms)} terms. Drafting translations with {TRANSLATE_MODEL} (this takes a few minutes)...")
    batches = [terms[i:i + 20] for i in range(0, len(terms), 20)]
    translations: dict[str, dict[str, str]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(_translate_batch, batches):
            translations.update(result)
            print(f"  translated {len(translations)}/{len(terms)}", flush=True)

    langs = [l for l in LANGUAGES if l != "en"]
    glossary = []
    for key in terms:
        e = chosen[key]
        tr = translations.get(key, {})
        glossary.append({
            "term": key,
            "snomed_id": "",            # to be looked up on termbrowser.nhs.uk
            "snomed_name": "",
            "category": e["category"],
            "frequency": freq.get(key, 0),  # number of BUILD consultations mentioning it
            "urgent": e["category"] == "urgent",
            "translations": {l: tr.get(l, "") for l in langs},
            "verified": {l: False for l in langs},  # true ONLY after a native speaker checks it
            "sources": e["sources"],
        })
    missing = [g["term"] for g in glossary if not all(g["translations"].values())]
    GLOSSARY.write_text(json.dumps(glossary, indent=2, ensure_ascii=False), encoding="utf-8")
    cats = Counter(g["category"] for g in glossary)
    print(f"Saved {GLOSSARY}: {len(glossary)} terms {dict(cats)}")
    if missing:
        print(f"WARNING: {len(missing)} terms have missing translations: {missing[:10]}")


if __name__ == "__main__":
    steps = {"split": split, "extract": extract, "build": build}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        print(__doc__)
        sys.exit(1)
    steps[sys.argv[1]]()
