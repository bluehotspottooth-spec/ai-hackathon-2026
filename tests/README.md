# `tests/`: how we tested VoiceBridge

**Written by:** Ahmed. Results live in `tests/results/`.

## What's in this folder

| File / folder | What it is |
|---|---|
| **`evaluate_medical.py`** | ⭐ **The medical test**: baseline vs VoiceBridge on medical sentences, all 11 languages. Results in `results/medical/` |
| `test_set_medical.csv` | The **93 test sentences** the medical test uses (from the 17 kept-aside consultations) |
| `make_medical_test_set.py` | Builds `test_set_medical.csv` from the kept-aside consultations |
| `build_glossary.py` | Builds our medical glossary (`backend/glossary.json`) from the **other 40** consultations |
| `primock57.py` | Helper that reads the PriMock57 transcripts |
| `results/medical/` | ⭐ **Medical test results** (start with its `README.md`) |
| `results/early_checks/` (`milestone1_urdu.json`, `milestone2/`) | Early checks while building (one Urdu clip; first spoken Urdu/Polish sentences) |
| `clips/` | Audio clips. `clips/recording/<language>/` is where teammates put their own recordings (native speakers) |

---

## 1. The data: PriMock57

[PriMock57](https://github.com/babylonhealth/primock57) (Babylon Health, licence CC BY 4.0) is **57 mock GP consultations** recorded in the UK: real doctors and actors playing patients, with full transcripts. It's the closest public data to what VoiceBridge is for: a UK GP appointment.

## 2. Why we kept 17 consultations aside

The hackathon rules say results must come from **test data not used to build the system**. Without that, a test only proves the system remembers what it was built from, like marking a student on the exact questions they revised.

So before building anything we **split the 57 consultations at random** (fixed seed 2026, so anyone gets the same split; the list is in [`data/split.json`](../data/split.json)):

| Group | Consultations | Used for |
|---|---|---|
| **BUILD** | 40 | Making the medical glossary: we found which medical terms GPs and patients actually use (106 terms, e.g. *fever, chest pain, antibiotic, metformin*) |
| **TEST** | 17 | **Only** for the final test. Never looked at while building |

The 17 TEST consultations: day1_consultation07, 08, 15; day2_consultation01, 06; day3_consultation02, 04, 07, 08; day4_consultation01, 02, 03, 04, 05, 07; day5_consultation03, 10.

## 3. The test sentences (`test_set_medical.csv`)

From the 17 TEST consultations only, `make_medical_test_set.py` picked sentences that:
- contain **at least one glossary term** (so there's a medical word to check);
- are 5–35 words long (no "yeah" lines, no long rambles);
- up to 3 per speaker per consultation, chosen at random (seed 2026).

That gave **93 sentences: 51 said by doctors, 42 by patients**. Example: *"OK. And how's your appetite? Are you eating and drinking OK?"* (term: appetite).

## 4. How the medical test works (`evaluate_medical.py`)

**Question:** do our additions (GP interpreter rules + medical glossary) make medical translation better than plain Gemini?

For **each of the 93 sentences** and **each of our 11 languages** (1,023 pairs), the same English sentence is translated **twice**, with the same AI model (`gemini-3.5-flash-lite`, the one the live app uses):

| | What it gets |
|---|---|
| **Baseline** | Just "Translate the following English text into Urdu" (etc.) |
| **VoiceBridge** | Our full GP interpreter rules + script rules + our medical glossary (the same instructions as the live app) |

Then each pair is scored three ways:
1. **Blind AI judge (main score).** A different model (`gemini-3.1-flash-lite`) sees the English and the two translations in **random order** as "A" and "B". It is never told which one is ours. For each, it says whether the **medical term is translated correctly**, gives an **accuracy score from 1 to 5** (negations, numbers, doses, body parts, anything added or missing), writes a note on any error, and picks the better one or a tie.
2. **Numbers kept:** every number in the English (e.g. *500*, *3*) must appear in the translation (in any script's digits).
3. **Glossary match:** does the translation use our glossary's word? This is only a consistency check: VoiceBridge is *given* the glossary, so it should score higher here.

**What this test does NOT cover (honest limits):**
- **Text only:** it tests the translation step, not speech recognition. The live app also hears the audio.
- **English → patient language only:** PriMock57 is in English. The other direction needs recordings by native speakers (`clips/recording/`).
- **The judge is an AI, not a native speaker.** Native speakers should check a sample of `results/medical/all_translations.csv`. The judge is also a small, fast model: we first tried the stronger `gemini-4-hydrogen`, but it needed ~55 s per pair (about 3 hours for the full test), too slow before the deadline. So treat the judge's scores as a first check.
- **Our glossary translations are AI-drafted and not yet checked** by native speakers.
- It doesn't test the safety features that only work on audio (noise check, "never invent", unclear words) or urgent flags. Those were tested by hand (see `docs/ERRORS_AND_FIXES.md`).

## 5. Run it yourself

From the `voicebridge` folder (uses the Gemini key in `.env`; no ElevenLabs credits):

```
.venv\Scripts\python -X utf8 tests\evaluate_medical.py                         # everything (1-3 hours: Google limits how fast we can call it)
.venv\Scripts\python -X utf8 tests\evaluate_medical.py --langs ur,ar --limit 5   # quick trial
```

It saves progress as it goes, so if it stops, run it again and it carries on. Results go to `results/medical/`.
