# Baseline comparison: plain Gemini vs VoiceBridge

The hackathon asks every project to **compare against a simple baseline**. This is ours.

- **Baseline:** plain Gemini (`gemini-3.5-flash-lite`), just told "translate this into <language>".
- **VoiceBridge:** the same model with what **we** added: GP interpreter rules (never soften or exaggerate symptoms, keep negations, doses and medicine names exact, never invent) and our **medical glossary** (106 terms from 40 PriMock57 consultations).

## The test data (kept aside)

Sentences from the **17 PriMock57 GP consultations we never used to build anything**. We split the 57 consultations at random (seed 2026) into 40 for building the glossary and 17 for testing only, so the test shows how VoiceBridge does on **new** conversations, not ones it was built from. More in [`README.md`](README.md), section 2.

Each sentence contains a medical term. The reported run covers **7 sentences** (*runny nose, appetite, antibiotic, diarrhoea, lisinopril, metformin, painkiller*), each translated into **all 11 languages** by both systems: **77 pairs**.

## How it was scored

A **blind AI judge** (a different model, `gemini-3.1-flash-lite`) saw the English sentence and the two translations in random order as "A" and "B", without knowing which was ours. For each it judged whether the medical term was correct, gave an accuracy score from 1 to 5, and noted errors. Then it picked the better one or a tie.

## Results

| | Plain Gemini (baseline) | VoiceBridge |
|---|---|---|
| Medical term translated correctly | 99% | **100%** |
| Accuracy (1–5) | 4.74 | **4.81** |
| Judge preferred it | 18% | **27%** (55% ties) |
| Used our glossary's word | 71% | **91%** |

**Per language** (accuracy 1–5, baseline → VoiceBridge):

| Better with VoiceBridge | Same | Worse with VoiceBridge |
|---|---|---|
| Polish 4.57 → 4.86 · Romanian 4.57 → 4.86 · Panjabi 4.86 → 5.0 · Portuguese 4.86 → 5.0 · Spanish 4.86 → 5.0 · Arabic 4.71 → 5.0 · Bengali 4.43 → 4.86 | Italian 4.86 → 4.86 | **Urdu 4.86 → 4.57 · Gujarati 4.71 → 4.57 · Persian 4.86 → 4.29** |

## What it shows

- **Where VoiceBridge helps:** in Bengali, the baseline misspelled the medicine *lisinopril* and VoiceBridge got it right. VoiceBridge was a little more accurate overall and used the same agreed medical words more consistently, so a symptom is always described the same way.
- **Where it fails:** in Urdu, Gujarati and Persian it was worse. It sometimes **left a word out** (Urdu: "eating and drinking" lost "drinking"), **changed the tense** (Gujarati: "I've got" became "I had"), or chose a **looser word** (Persian: "sniffles" became "you've caught something").
- **What this test can't show:** our main safety features need audio: refusing noisy recordings (the AI invented symptoms in noise), urgent-symptom flags and unclear-word warnings. Those were tested by hand (see `docs/ERRORS_AND_FIXES.md`).

## Limits

Small test (7 sentences per language: Google's rate limits made the full 93-sentence run 2–3 hours). The judge is an AI, not a native speaker. Text only, English → patient language. Our glossary translations are AI-drafted and not yet checked by native speakers.

**Full results:** [`results/medical/`](results/medical/): the table per language, every translation with the judge's notes, and side-by-side examples. **Script:** [`evaluate_medical.py`](evaluate_medical.py).
