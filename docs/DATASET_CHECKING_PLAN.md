# Dataset checking plan

How we build the medical glossary, how we check it against the NHS standard, and how we test VoiceBridge fairly.
For the **testing teammate** (steps C1–C3 in docs/PROJECT_BRIEF.md), but everyone should understand it, because judges will ask.

> **The one rule that matters most:** never test on data that was used to build the system.
> The hackathon rules say results must come from **test data not used to build the system**.

---

## 1. The datasets we use

| Dataset | What it is | What we use it for | Licence (credit it!) |
|---|---|---|---|
| **PriMock57** ([github.com/babylonhealth/primock57](https://github.com/babylonhealth/primock57)) | 57 mock UK GP appointments (real clinicians as doctors, actors as patients): audio, transcripts, notes | **40** to build the glossary, **17** kept aside for the medical test | CC BY 4.0. Cite: Papadopoulos Korfiatis et al., ACL 2022 |
| **SNOMED CT** ([termbrowser.nhs.uk](https://termbrowser.nhs.uk/)) | The NHS's official medical vocabulary (350,000+ terms, English) | **Checking** the official English name + code of every glossary term | Free to search online. We only look terms up; we don't download or redistribute it |
| **FLEURS** (google/fleurs on Hugging Face) | Real people reading sentences in 100+ languages, incl. all 11 of ours | The general speech test (C2) | CC BY 4.0 |
| **FLORES+** (openlanguagedata/flores_plus) | The correct translations of the same sentences | English reference answers for C2 | CC BY-SA 4.0 (needs a free Hugging Face login) |
| **ONS Census 2021** | Most-spoken languages in England & Wales | Choosing our 10 languages | Open Government Licence |

---

## 2. Why we keep 17 PriMock57 appointments aside

```
PriMock57: 57 GP appointments
   ├── 40 "BUILD" appointments → we take medical words from these to make the glossary
   └── 17 "TEST" appointments  → locked away; only used at the end to test VoiceBridge
```

**Why:** if we built the glossary from *all* 57 and then tested on them, every medical word in the test would already be on our cheat sheet. VoiceBridge would look much better than it really is. It's like writing an exam, giving students the answers, and then being surprised they scored 100%.
Testing on 17 appointments the glossary has **never seen** shows how it does on new conversations, like a real GP surgery.

**Why 40 / 17?** About 70% for building and 30% for testing, a common split. 40 appointments is enough to find the frequent GP words, and 17 still gives hundreds of test sentences.

**How to split fairly:**
- Shuffle the 57 consultation IDs **randomly with a fixed seed** (e.g. `random.seed(2026)`), so anyone can repeat it, and take the first 40 as BUILD.
- **Save the lists** in `data/split.json`: `{"build": [...40 IDs...], "test": [...17 IDs...]}` and commit it. This is our proof.
- After that, **nobody looks at the 17 TEST appointments** until the final test. Not to pick words, not to tweak prompts.

**Same rule for FLEURS:** Urdu clips **1806 and 1930** were used while building (Milestone 1 and the script fix), so they're **excluded** from the C2 test.

---

## 3. Building the glossary (~80–100 terms)

40 terms alone is a bit few, but every term has to be translated into 11 languages (100 terms = 1,100 translations), so we choose terms **smartly**, not just "more".

### Where the terms come from (BUILD appointments only)

| Category | How to find them | About | `category` value |
|---|---|---|---|
| **Frequent GP words** | Gemini lists the medical terms in each of the 40 BUILD transcripts; count how many appointments mention each; keep the top ones | 40–50 | `frequent` |
| **Urgent / red-flag symptoms** | NHS "call 999 / go to A&E" warning signs (chest pain, can't breathe, stroke signs, severe bleeding, suicidal thoughts, sepsis signs, anaphylaxis…). Start from the 13 in `backend/prompts.py` | 15–20 | `urgent` |
| **Common UK GP medicines** | e.g. paracetamol, ibuprofen, amoxicillin, omeprazole, salbutamol inhaler, metformin, sertraline… (also check which ones appear in the BUILD transcripts) | 10–15 | `medicine` |
| **Words plain Gemini gets wrong** | Run the **baseline** on doctor/patient lines from the **BUILD** appointments only, and note medical words it mistranslates | whatever we find | `baseline_error` |

### Checking each term against the NHS standard (SNOMED CT)
For every English term:
1. Search it on [termbrowser.nhs.uk](https://termbrowser.nhs.uk/).
2. Write down the **official preferred term** and its **SNOMED CT ID** (the number).
3. If our word is informal (e.g. "tummy ache"), keep the everyday word as `term` (that's what people say) and put the official one in `snomed_name`.
4. No match? Leave `snomed_id` empty and add a note. That's fine.

### Translating and verifying
1. Gemini drafts the translation of each term into the 11 languages.
2. **A native speaker checks** where we have one (Persian; plus any other languages the team or their families speak).
3. Mark `verified: true` for a language **only if a real speaker checked it**. Never mark AI-only translations as verified.
4. In the write-up, say honestly how many translations were checked per language.

### `backend/glossary.json` format
The testing teammate saves the file into `backend/` (the one file in Ahmed's folder they write to; agreed). Example entry:
```json
{
  "term": "chest pain",
  "snomed_id": "29857009",
  "snomed_name": "Chest pain",
  "category": "urgent",
  "frequency": 12,
  "urgent": true,
  "translations": { "ur": "سینے میں درد", "pl": "ból w klatce piersiowej", "...": "..." },
  "verified":     { "ur": true, "pl": false, "...": false },
  "sources": ["PriMock57 build set", "NHS red flags", "SNOMED CT browser"]
}
```
*(The SNOMED ID above is an example. Look up and confirm every ID yourself.)*

### How the backend uses it (already built; two small upgrades pending)
- `prompts.py` already adds the glossary to Gemini's instructions automatically when the file exists.
- **Pending backend change (Ahmed):** only send translations marked `verified: true` for that language, plus all English terms. An unchecked wrong translation could make things worse.
- **Pending backend change (Ahmed):** add all `urgent: true` terms to the urgent-flag list.

---

## 4. How we test

### C2: General speech test (FLEURS), all 11 languages
- About **20 clips per language** from the FLEURS **test** split (excluding Urdu 1806 and 1930).
- Measure **per language**: language detection accuracy, transcription error (character error rate, `jiwer`), translation quality vs the FLORES+ English reference (`chrF`, `sacrebleu`), and time taken.
- **Speech credits:** these tests don't need the ElevenLabs voice. Test the translation only (`translate_audio`), which uses Gemini, not our limited voice credits.

### C3: Medical test, baseline vs VoiceBridge (the most important one)
Uses the **17 TEST appointments only**.
- **Doctor → patient:** take doctor lines (English), translate into each language. Check: are the glossary terms translated correctly (using **verified** entries)?
- **Patient → doctor:** patient lines spoken in other languages, either recorded by teammates who speak them (best: real voices, with their consent) or generated with an AI voice from a verified translation (clearly labelled as synthetic). Then translate to English and check the medical meaning survived.
- Run **every sentence twice**: `use_medical_layer=False` (baseline) and `True` (VoiceBridge).
- **Native speakers rate** both versions 1–5 **without knowing which is which** (shuffle them and label them A/B).
- Save side-by-side examples: input | baseline | VoiceBridge | correct translation, **including failures**.

### Results we report
- A table **per language** (never one average for everything).
- Baseline vs VoiceBridge for each metric.
- Honest "where it fails" examples, e.g. the Urdu "released → burnt to death" mis-hearing and the invented symptoms in noise (see `ERRORS_AND_FIXES.md`).

---

## 5. Checklist

- [ ] PriMock57 downloaded (needs Git LFS for the audio) and licence noted
- [ ] `data/split.json` created with a fixed seed and committed (40 BUILD / 17 TEST)
- [ ] Terms extracted from the 40 BUILD transcripts → `data/term_counts.csv`
- [ ] Urgent terms, medicines and baseline-error terms added (~80–100 total)
- [ ] Every term checked on the NHS SNOMED CT browser (ID + official name)
- [ ] Translations drafted; native-speaker checks done where possible; `verified` set honestly
- [ ] `backend/glossary.json` saved and pushed; Ahmed told so he can switch on "verified only"
- [ ] C2 FLEURS test run (excluding Urdu 1806, 1930), results per language in `tests/results/`
- [ ] C3 medical test run on the 17 TEST appointments, blind native-speaker ratings collected
- [ ] All datasets credited with links and licences in the write-up
