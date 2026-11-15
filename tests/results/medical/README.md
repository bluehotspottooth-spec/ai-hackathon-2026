# Medical test results: baseline vs VoiceBridge

**Question:** do our additions (GP interpreter rules + medical glossary) translate medical sentences better than plain Gemini?

**Short answer:** slightly better overall on this small test, but **not in every language**. VoiceBridge scored higher in 7 of 11 languages and **lower in 3 (Urdu, Gujarati, Persian)**. Both systems got almost every medical word right; the differences are mostly in how complete and natural the rest of the sentence is.

## What we tested

- **Sentences:** 7 sentences said in real-style UK GP consultations (4 by doctors, 3 by patients), each containing a medical term: *runny nose, appetite, antibiotic, diarrhoea, lisinopril, metformin, painkiller*.
- **From data we kept aside:** they come from the **17 PriMock57 consultations we never used to build anything** (see [`tests/README.md`](../../README.md), section 2, for why and how they were kept aside).
- **11 languages × 7 sentences = 77 pairs.** Every language was tested on exactly the same 7 sentences.
- **Each pair:** the same English sentence translated by **plain Gemini (baseline)** and by **VoiceBridge** (same model, `gemini-3.5-flash-lite`, plus our GP rules and glossary).
- **Scored by a blind AI judge** (`gemini-3.1-flash-lite`, a different model): it saw the two translations in random order as A and B, never told which was ours. For each it judged the medical term (correct or not), gave an accuracy score from 1 to 5, and noted any errors. Then it picked the better one or a tie.

**Why only 7 sentences?** The full test set has 93 sentences (1,023 pairs), and the script can run all of them. Google limited how fast we could send requests, so the full run would have taken 2–3 hours. We stopped once 7 sentences were finished in all 11 languages, so every language is compared fairly on the same sentences. With 7 sentences per language, **one sentence changes a language's score by about 14%**, so treat per-language differences as signals, not proof.

## Results per language

| Language | Term correct: baseline | Term correct: VoiceBridge | Accuracy (1-5): baseline | Accuracy (1-5): VoiceBridge | Judge prefers VoiceBridge | Judge prefers baseline | Tie | Glossary word used: baseline | Glossary word used: VoiceBridge |
|---|---|---|---|---|---|---|---|---|---|
| Polish (pl) | 100% | 100% | 4.57 | 4.86 | 43% | 14% | 43% | 71% | 86% |
| Romanian (ro) | 100% | 100% | 4.57 | 4.86 | 29% | 14% | 57% | 57% | 86% |
| Panjabi (pa) | 100% | 100% | 4.86 | 5.0 | 29% | 0% | 71% | 71% | 86% |
| Urdu (ur) | 100% | 100% | 4.86 | **4.57** | 14% | **43%** | 43% | 29% | 100% |
| Portuguese (pt) | 100% | 100% | 4.86 | 5.0 | 14% | 0% | 86% | 100% | 100% |
| Spanish (es) | 100% | 100% | 4.86 | 5.0 | 14% | 14% | 71% | 86% | 100% |
| Arabic (ar) | 100% | 100% | 4.71 | 5.0 | 43% | 0% | 57% | 57% | 71% |
| Bengali (bn) | **86%** | 100% | 4.43 | 4.86 | 57% | 14% | 29% | 43% | 86% |
| Gujarati (gu) | 100% | 100% | 4.71 | **4.57** | 29% | **43%** | 29% | 71% | 86% |
| Italian (it) | 100% | 100% | 4.86 | 4.86 | 29% | 14% | 57% | 100% | 100% |
| Persian (fa) | 100% | 100% | 4.86 | **4.29** | 0% | **43%** | 57% | 100% | 100% |
| **ALL LANGUAGES** | **99%** | **100%** | **4.74** | **4.81** | **27%** | **18%** | **55%** | **71%** | **91%** |

*"Term correct" and "accuracy" come from the blind judge. "Glossary word used" is an automatic check of whether the translation uses our glossary's word; VoiceBridge is given the glossary, so it's expected to be higher there. None of the 7 sentences contained a number, so the numbers check doesn't apply.*

## What it means

1. **Plain Gemini is already good at medical words.** The baseline translated the key term correctly in 76 of 77 pairs. The one miss: in **Bengali** it misspelled the medicine **lisinopril** ("Lisinoprefil"); VoiceBridge got it right.
2. **VoiceBridge was slightly more accurate overall** (4.81 vs 4.74 out of 5), and the judge preferred it more often (27% vs 18%; 55% ties). It also used our agreed glossary words more consistently (91% vs 71%), which matters so the same symptom is always described the same way.
3. **It was worse in Urdu, Gujarati and Persian.** The judge's notes (in [`all_translations.csv`](all_translations.csv); some are in [`examples.md`](examples.md)) show why: VoiceBridge sometimes **left something out** (Urdu: "eating and drinking" lost "drinking"), **changed the tense** (Gujarati: "I've got" became "I had"), or translated a vague word too loosely (Persian: "sniffles" became "you've caught something"). Our rule to "interpret faithfully and naturally" seems to make it shorten or smooth some sentences.
4. **What this test can't show:** most of what we added protects patients in ways a text test doesn't measure: refusing to translate noisy audio (the AI invented symptoms in noise), flagging urgent symptoms like chest pain, and warning about unclear words. Those were tested by hand; see `docs/ERRORS_AND_FIXES.md`.

## Honest limits

- **Small:** 7 sentences per language, from 2 of the 17 kept-aside consultations.
- **The judge is an AI, not a native speaker,** and a small, fast model (a stronger one needed ~55 s per pair, too slow before the deadline). Native speakers should check the translations in `all_translations.csv`.
- **Text only, English → patient language only.** It tests the translation step, not speech recognition, and not the patient → English direction (that needs recordings by native speakers).
- **Our glossary translations are AI-drafted** and not yet checked by native speakers.

## Files

| File | What it is |
|---|---|
| [`results_by_language.csv`](results_by_language.csv) | The table above, as a spreadsheet |
| [`all_translations.csv`](all_translations.csv) | **Every pair:** English, baseline, VoiceBridge, the judge's scores and notes. Open in Excel or Google Sheets |
| [`examples.md`](examples.md) | Side-by-side examples: where VoiceBridge did better, and **where it did worse** |
| `raw_results.jsonl` | Raw output of the script (also includes 58 pairs from sentences not finished in all languages, which are **not** counted above) |

To run the full 93-sentence test: `.venv\Scripts\python -X utf8 tests\evaluate_medical.py` (it continues from these results).
