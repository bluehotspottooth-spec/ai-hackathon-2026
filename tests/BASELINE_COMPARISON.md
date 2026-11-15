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

## Safety checks: what plain Gemini does vs VoiceBridge

The text test above can't show our main additions, because they're about **audio** and **patient safety**. While building, we tested these dangers on purpose. Each row compares plain Gemini with VoiceBridge **after our fixes**.

| Danger | Plain Gemini (baseline) | VoiceBridge | How we tested |
|---|---|---|---|
| **Heavy background noise:** the AI can't hear, so it guesses | ❌ **Invented symptoms** that were never said ("my throat is very bad and I have a cough", 1 of 2 runs). Nothing stops noisy audio | ✅ A **noise check** (plain maths, no AI) **blocks** very noisy recordings and asks the speaker to repeat. Even when noisy audio is sent straight to the AI, it now answers **"inaudible": 4 of 4 runs**. *(Before our fix, VoiceBridge itself invented "sharp chest pain" in 2 of 2 runs: our "GP appointment" instructions made the guess medical)* | Pink noise added to a speech clip, re-run several times · errors log #23 |
| **Urgent symptoms** (chest pain, can't breathe…) | ❌ No warning at all | ✅ **Red urgent banner** for the GP when the patient **reports** a symptom. **No false alarm** when the doctor only **asks** ("Do you have any shortness of breath?") or the patient denies it | Real turns through the live app · errors log #35 |
| **Exaggeration:** "a tight pain in my chest" | No rule against it | ✅ Rule: never add intensity words. Before the rule, VoiceBridge said "**severe** pain" in Urdu; after it, "tightness" (جکڑن), **no "severe", 3 of 3 runs** | Errors log #30, #32, #35 |
| **Wrong alphabet:** Urdu written in Hindi or Roman letters | ❌ Wrote the Urdu transcript in **Roman letters** | ✅ Script rules per language: **Urdu script 6 of 6 runs** | 2 Urdu FLEURS clips, 3 runs each · errors log #16 |
| **Confidently mis-heard word:** Urdu *rihaa* ("released") heard as *jalaa* ("burnt") | ❌ "…were **burnt to death**" | ❌ **Also fails** (3 of 3 runs), and the AI's own "I'm not sure" signal flagged nothing (0 of 3). **Our safeguard:** the speaker always sees what was heard in their own language, with a **"Not what I said"** button | Errors log #14, #22 |
| **Background noise the speaker might not notice** | No warning | ✅ "Background noise" badge on the message when our check measures some noise | Errors log #23 |

**Honest note:** these were tested on our own **development clips** (2 FLEURS Urdu clips, AI voices and live turns), a few runs each, while building and fixing. They are **not** results on the kept-aside test data. They show *what* each safety feature does, not *how often* it works across many conversations.

## Limits

Small test (7 sentences per language: Google's rate limits made the full 93-sentence run 2–3 hours). The judge is an AI, not a native speaker. Text only, English → patient language. Our glossary translations are AI-drafted and not yet checked by native speakers.

**Full results:** [`results/medical/`](results/medical/): the table per language, every translation with the judge's notes, and side-by-side examples. **Script:** [`evaluate_medical.py`](evaluate_medical.py).
