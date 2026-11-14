# VoiceBridge: project brief for Claude Code

Read this whole file before doing anything. It is the single source of truth for this project.

## 1. Who we are and how to work with us

- We are a team of 3 UK high-school students (Year 12) in the **Veritas AI International High School Hackathon 2026**, a 48-hour online hackathon.
- **Deadline:** Monday 16 Nov 2026, 4:59 AM London time (11:59 PM ET Sunday). We aim to submit on **Sunday evening**.
- This is our **first real project**. We know basic Python and what API keys are, but we have never connected APIs, built a backend, or deployed anything.
- Machine: **Windows 11, PowerShell, Python 3.12, Git, VS Code, ffmpeg** installed.

**Rules for you (Claude Code):**
1. Work in **small steps**. Do one step, run it, show the result, then stop and wait for us to say "next".
2. After writing each file or function, **explain in plain English** what it does and why. We must be able to explain every part to judges in a live Q&A.
3. **Ask before** installing packages, deleting anything, or changing the API contract (section 6).
4. Never put API keys in code. Keys live in `.env` (which must be in `.gitignore` before the first commit) and in Hugging Face Secrets when deployed.
5. **Commit to Git after every working step** with a clear message. Our commit history is our evidence that everything was built during the hackathon.
6. Check the **current official docs** for model names and SDK usage (Gemini, ElevenLabs) rather than guessing. Tell us which model you chose and why.
7. Prefer simple, readable code over clever code. Add short comments.
8. If something fails twice, stop and explain the problem and the options.

## 2. Hackathon rules that affect the code

- All project code must be written during the hackathon (Sat 14 Nov 5:00 AM to Mon 16 Nov 4:59 AM London).
- **AI must be central** to the project.
- Allowed: public datasets, pretrained models, AI APIs, open-source libraries, coding assistants. **Everything must be credited** in the write-up with links.
- When building on an LLM API, judges focus on **what we add around it: our data, how we tested it, and who it is for**.
- Required in every project: name one specific user; show a real input producing a result; **compare against a simple baseline**; show **where it fails** and why.
- Results must come from **test data not used to build the system**.
- Languages track: report results **separately for each language**; show **our output next to the correct output**; checks by a **real speaker** of the language; only use public datasets or our own voices (no one else's voice without permission).
- Report honest results, including weak ones.
- Add the line: "This project is a prototype and is not medical advice."
- Submission: GitHub repo + one-page write-up (Veritas template) + optional 2-minute demo video + credits.

## 3. The product

**VoiceBridge** is a live voice translator for **GP appointments in the UK**.

- **User:** a patient with limited English who needs to explain their symptoms to a GP (and understand the GP's answers).
- **What goes in:** the patient speaks in their language (or the doctor speaks English).
- **What comes out:** the other person hears the translation spoken aloud a few seconds later, with a live two-language transcript on screen.
- **Track:** AI + Languages ("help people understand each other, especially in a language technology serves poorly").

**Languages:** the 10 most common main languages in England and Wales after English (ONS Census 2021): Polish, Romanian, Panjabi, Urdu, Portuguese, Spanish, Arabic, Bengali, Gujarati, Italian. Plus Persian (a teammate speaks it). English is always one side.

**What we add on top of the AI (our "own work"):**
1. A **medical glossary** built from real-style UK GP consultations (PriMock57), checked against official NHS terms (SNOMED CT browser) and, where possible, by native speakers.
2. A **GP-specific translation prompt** (keep medical terms exact, never soften symptoms, flag urgent phrases).
3. **Urgent-term flags** (e.g. chest pain, can't breathe) shown in red to the doctor.
4. **Testing across 11 languages** against a baseline, with failures shown.
5. **Optional, only if time allows:** voice cloning of a speaker's own voice with recorded consent (our team's voices only). Core app uses a good stock voice.

## 4. Architecture

```
Gradio UI (frontend/app.py)            /api endpoints (backend/main.py)
   │  records mic, calls Python          │  used by /docs testing and the
   │  functions directly                 │  evaluation scripts
   └──────────────┬──────────────────────┘
                  ▼
        backend/service.py   create_session, run_turn, get_summary, end_session
                  │          (one place for the logic, so nothing is written twice)
   ├─ audio.py     convert any audio -> wav with pydub + ffmpeg
   ├─ pipeline.py  Gemini: transcribe + detect language + translate (JSON output)
   ├─ voice.py     text-to-speech (ElevenLabs multilingual; fallback Gemini TTS); optional cloning
   └─ sessions.py  in-memory sessions, access code, turn limit
                  ▼
Hosted on Hugging Face Spaces (Docker, port 7860): FastAPI app with the Gradio UI
mounted on it (gr.mount_gradio_app), so one public link serves both.
```

**Decision (Sat 14 Nov, under review):** the frontend was switched to **Gradio** (brief: `docs/UI_BRIEF_GRADIO.md`). A teammate has since made an HTML/CSS/JS mockup in Gemini Canvas (`frontend/mockup/`), so going back to HTML (brief: `docs/UI_BRIEF.md`) is being considered. The backend supports both: the `service.py` functions return the same fields as the `/api` endpoints in section 6.

**Who owns which folder** (see README): `backend/` + top-level setup files = Ahmed; `frontend/` = UI teammate; `tests/` + `data/` = testing teammate; `docs/` = shared. Only edit your own folder.

## 5. Folder structure

```
voicebridge/
  CLAUDE.md
  README.md         (includes "who works where")
  docs/
    UI_BRIEF.md                    (HTML frontend brief)
    UI_BRIEF_GRADIO.md             (Gradio frontend brief)
    Submission for Hackathon.docx  (write-up)
  requirements.txt
  Dockerfile
  .env              (never committed)
  .env.example      (committed: lists the keys, no real values)
  .gitignore
  backend/
    main.py
    service.py
    audio.py
    pipeline.py
    prompts.py
    voice.py
    sessions.py
    glossary.json
  frontend/
    mockup/           (original Gemini Canvas HTML mockup, credited)
    app.py            (Gradio UI, exposes `demo`)
    mock_service.py   (fake service functions for building the UI)
  data/
    primock57/      (downloaded dataset, gitignored if large)
    term_counts.csv
  tests/
    build_glossary.py
    evaluate_fleurs.py
    evaluate_medical.py
    test_set_medical.csv
    clips/
    results/
```

## 6. API contract (agree before building; change only with the team's approval)

All endpoints are under `/api`. All responses are JSON. Errors return `{"error": "<message>"}` with a suitable HTTP status.

| Endpoint | Request (multipart/form-data unless noted) | Response |
|---|---|---|
| `POST /api/session` | JSON: `access_code`, `doctor_lang` ("en"), `patient_lang` (e.g. "ur") | `{session_id, turns_left}` |
| `POST /api/clone` *(optional feature)* | `session_id`, `speaker` ("doctor"/"patient"), `consent` (true/false), `audio` file | `{voice_ready: true, cloned: true/false}` |
| `POST /api/turn` | `session_id`, `speaker` ("doctor"/"patient"), `audio` file | `{original_text, detected_language, target_language, translation, urgent_terms: [..], audio_base64 (mp3), timings: {convert, translate, speak, total}, turns_left}` |
| `POST /api/summary` | JSON: `session_id` | `{summary_en, summary_patient_lang}` |
| `POST /api/end` | JSON: `session_id` | `{ended: true}` (deletes any cloned voices) |

Rules:
- Wrong access code → 401. More than 20 turns per session → 429 with a friendly message.
- `speaker` decides the direction: patient speaks → translate to English; doctor speaks → translate to `patient_lang`.
- `detected_language` is still reported (auto-detect) and shown in the UI; if it differs from the expected language, show a warning.
- A config flag `USE_MEDICAL_LAYER` (glossary + GP prompt) must exist so tests can switch it off for the **baseline**.

## 7. The three parts

### PART A: Backend (Malik)

Build in this order. Each phase ends with a milestone that must work before moving on.

**A1. Setup**
- Create the folder structure, `.gitignore` (include `.env`, `.venv/`, `__pycache__/`, large data), virtual environment, `requirements.txt` (fastapi, uvicorn[standard], python-multipart, google-genai, elevenlabs, python-dotenv, pydub, gradio (approved for the Gradio frontend); add others only with approval). Versions are pinned in `requirements.txt`.
- `.env` keys: `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`, `ACCESS_CODE`.

**A2. `audio.py`**
- Convert any uploaded audio (browser webm/opus, wav, mp3, m4a) to a format Gemini accepts, using pydub + ffmpeg. Reject empty or very short clips with a clear error.

**A3. `pipeline.py` + `prompts.py` (Gemini)**
- `translate_audio(audio_bytes, source_hint, target_lang, use_medical_layer=True)` → dict with `original_text`, `detected_language`, `translation`, `urgent_terms`.
- Use Gemini's structured JSON output.
- Medical layer = GP prompt + glossary terms relevant to the target language. Baseline = plain "transcribe, detect language, translate" prompt.
- Time each call.
- **Milestone 1:** run on a FLEURS Urdu clip from the terminal and print the JSON.

**A4. `voice.py` (speech)**
- `speak(text, language, voice_id=None)` → mp3 bytes using a multilingual model. Stock voice by default.
- Check which of our 11 languages the chosen TTS supports; for unsupported ones fall back to another TTS (e.g. Gemini TTS) or text-only, and record this honestly.
- Optional later: `clone_voice(sample, name)` and `delete_voice(voice_id)`.
- **Milestone 2:** generate and play an Urdu and a Polish sentence.

**A5. `sessions.py`**
- In-memory dict: `session_id → {doctor_lang, patient_lang, voices, turns[], turn_count, created_at}`. Access code check. 20-turn limit. Sessions are lost on restart (fine for a prototype).

**A6. `service.py` + `main.py` (FastAPI)**
- `service.py`: the 4 functions from `docs/UI_BRIEF_GRADIO.md` section 4 (`create_session`, `run_turn`, `get_summary`, `end_session`) plus `ServiceError`, calling A2 to A5.
- `main.py`: implement the contract in section 6 by calling `service.py`.
- Mount the Gradio `demo` from `frontend/app.py` at `/` with `gr.mount_gradio_app`.
- Run with `uvicorn backend.main:app --reload`.
- **Milestone 3:** full turn works from `http://localhost:8000/docs` by uploading an audio file.

**A7. Extras (only after the frontend is connected)**
- `/api/summary` (Gemini text call over saved turns, in both languages).
- Urgent-term detection in the response.
- Optional voice cloning with consent.

**A8. Deploy**
- `Dockerfile`: Python 3.12 slim, install ffmpeg via apt, install requirements, run uvicorn on port 7860.
- Hugging Face Space (Docker SDK); keys in Space Secrets.
- **Milestone 5:** the public link works on a phone (mic permission, a full conversation, access code, limit).

### PART B: Frontend / UI (teammate, in Gradio)

**The full frontend brief is `docs/UI_BRIEF_GRADIO.md`** (or `docs/UI_BRIEF.md` if we switch back to HTML). Summary:
- Gradio `gr.Blocks` app in `frontend/app.py`, exposed as `demo`, with 4 screens: access, language setup, appointment (doctor mic, patient mic, shared transcript, urgent flags, turns left), summary.
- Calls the 4 `service.py` functions. `USE_MOCK = True` uses `frontend/mock_service.py` until the backend is ready.
- Footer line: "This project is a prototype and is not medical advice."
- Known Gradio limits: click-to-record (not hold-to-speak); iPhone autoplay may need a tap.

### PART C: Testing, data and evidence (teammate, with help)

All results go in `tests/results/` as CSV files and are summarised in the write-up and README. **Report every metric per language.**

**C1. Glossary from PriMock57 (`tests/build_glossary.py`)**
- Dataset: https://github.com/babylonhealth/primock57 (57 mock UK primary-care consultations: audio, transcripts, notes). Check its licence and credit it.
- **Split the consultations:** about 40 for building the glossary, about 17 held out for testing (record which IDs). Never test on glossary-building consultations.
- Extract medical terms from the 40 transcripts (Gemini: "list the medical terms in this conversation"), count how many consultations mention each, save `data/term_counts.csv`.
- Take the top 40 to 50 terms. Check official English names in the NHS SNOMED CT browser (https://termbrowser.nhs.uk/). Mark urgent terms.
- Create translations for each language; mark each entry `verified: true` only if a native speaker checked it. Save `backend/glossary.json` with fields: term, snomed_id (if found), frequency, urgent, translations {lang: text}, verified {lang: bool}, sources.

**C2. General speech translation across languages (`tests/evaluate_fleurs.py`)**
- Data: FLEURS (google/fleurs on Hugging Face) test split, about 20 clips per language for our 11 languages; English reference translations from the same sentence IDs in FLORES+ (or the English FLEURS transcripts of the same IDs).
- Measure per language: language detection accuracy; transcription error (character error rate with `jiwer`); translation quality to English with **chrF** (`sacrebleu`); latency.
- This shows where VoiceBridge works well and where it fails across languages.

**C3. Medical test with baseline (`tests/evaluate_medical.py`)**
- Test sentences: doctor and patient lines taken from the **held-out** PriMock57 consultations, plus patient-style sentences our team writes/records in languages we speak (Persian, and any others teammates speak).
- Run each sentence twice: `USE_MEDICAL_LAYER=False` (**baseline**) and `True` (**VoiceBridge**).
- Measure: medical terms translated correctly (using verified glossary entries), chrF against reference translations where a native speaker wrote one, and native-speaker ratings 1 to 5 (blind to which version produced it).
- Save side-by-side examples (input, baseline output, VoiceBridge output, correct output), including failures.

**C4. Voice and usability**
- Latency per step (convert, translate, speak, total) per language.
- If cloning is enabled: 3 listeners rate stock vs cloned voice 1 to 5 (team voices only, with consent).
- 3 to 5 people try the live app; note confusing moments and time to complete a short conversation.
- Limit and safety checks: wrong access code, 21st turn, consent declined, cloned voices deleted at session end.

**C5. Evidence and deliverables**
- Results tables and one or two charts (e.g. chrF per language, baseline vs VoiceBridge).
- "Known limitations" list with real failure examples and our explanation.
- Credits list: every dataset, model, API, library and AI tool (Gemini, ElevenLabs, PriMock57, FLEURS, FLORES+, SNOMED CT browser, ONS Census 2021, FastAPI, pydub, jiwer, sacrebleu, Claude) with links and licences.
- One-page write-up (Veritas template), 2-minute demo video, showcase page.

## 8. Timeline (London time)

| When | Target |
|---|---|
| Sat morning | A1 to A3 done (Milestone 1). UI design tokens + HTML. PriMock57 downloaded and split. |
| Sat afternoon | A4 to A6 (Milestones 2 and 3). UI with mock backend. Glossary terms extracted. |
| Sat evening | Frontend connected to real backend (Milestone 4). Glossary drafted. |
| Sun morning | Extras (summary, urgent flags). Deploy (Milestone 5). FLEURS evaluation running. |
| **Sun 1 PM** | **Feature freeze.** Only bug fixes after this. |
| Sun afternoon | Medical baseline test, ratings, results tables, write-up, video, showcase page. |
| Sun evening | Submit. Resubmit improvements if needed before 4:59 AM Monday. |

## 9. Start now

Begin with **Part A, step A1** only. Create the folders, `.gitignore`, virtual environment and `requirements.txt`, explain each one, then stop and wait for "next".
