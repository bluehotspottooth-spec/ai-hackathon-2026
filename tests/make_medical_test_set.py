"""
make_medical_test_set.py: builds tests/test_set_medical.csv for the medical test (C3).

It takes sentences ONLY from the 17 TEST consultations in data/split.json
(never the 40 used to build the glossary), and keeps the ones that contain at
least one glossary term, so we can check whether medical words are translated
correctly. Run:  python -X utf8 tests/make_medical_test_set.py

Each row is one sentence:
  id, consultation_id, speaker, direction, text_en, glossary_terms
direction: doctor lines are translated English -> patient language;
           patient lines are first spoken in the patient language (by a teammate
           or a labelled AI voice), then translated back to English.
"""

import csv
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import primock57  # noqa: E402

SEED = 2026
PER_SPEAKER_PER_CONSULTATION = 3   # 17 consultations x 2 speakers x 3 = up to 102 sentences
MIN_WORDS, MAX_WORDS = 5, 35       # skip tiny "yeah" lines and long rambles

split = json.loads((ROOT / "data" / "split.json").read_text())
glossary = json.loads((ROOT / "backend" / "glossary.json").read_text(encoding="utf-8"))
terms = sorted({g["term"] for g in glossary}, key=len, reverse=True)
patterns = {t: re.compile(r"\b" + re.escape(t) + r"s?\b", re.I) for t in terms}

rng = random.Random(SEED)
rows = []
for cid in split["test"]:
    for speaker in ("doctor", "patient"):
        candidates = []
        for u in primock57.utterances(cid):
            if u["speaker"] != speaker or not (MIN_WORDS <= len(u["text"].split()) <= MAX_WORDS):
                continue
            found = [t for t, p in patterns.items() if p.search(u["text"])]
            if found:
                candidates.append((u["text"], found))
        for text, found in rng.sample(candidates, min(PER_SPEAKER_PER_CONSULTATION, len(candidates))):
            rows.append({
                "id": f"M{len(rows) + 1:03d}",
                "consultation_id": cid,
                "speaker": speaker,
                "direction": "en->patient_lang" if speaker == "doctor" else "patient_lang->en",
                "text_en": text,
                "glossary_terms": "; ".join(found),
            })

out = ROOT / "tests" / "test_set_medical.csv"
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"Saved {out}: {len(rows)} sentences from {len(split['test'])} TEST consultations "
      f"({sum(r['speaker'] == 'doctor' for r in rows)} doctor, {sum(r['speaker'] == 'patient' for r in rows)} patient)")
