# VoiceBridge

A live voice translator for **GP appointments in the UK**: a patient with limited English and their GP speak in their own languages and hear each other's words translated aloud, with a two-language transcript on screen.

Built for the Veritas AI International High School Hackathon 2026 (AI + Languages track).

> This project is a prototype and is not medical advice.

---

## Who works where

**Rule: only edit files in your own folder.** That way we never overwrite each other's work. If you need something changed in someone else's folder, ask them.

| Folder | Owner | What goes in it |
|---|---|---|
| `backend/` | **Ahmed** | Python server: audio conversion, Gemini translation, speech, sessions, API |
| `frontend/` | **Benet** | The web app people see: `voicebridge_FINAL.html` (start with `frontend/README.md`). `frontend/old_mockup/` holds the OLD first Gemini Canvas mockup (reference only) |
| `tests/` and `data/` | **Testing teammate** | Glossary building, FLEURS + medical evaluations, results CSVs, charts |
| `docs/` | **Everyone** | Briefs and the write-up. Say in the team chat before editing a shared doc |
| `deploy/` (`Dockerfile`, `requirements.txt`) and `.gitignore` | **Ahmed** | Project setup. Ask Ahmed if you need a package added |

### Uploading through the GitHub website
1. Open **your** folder on GitHub first (e.g. click `frontend`).
2. Then **Add file → Upload files**. The files land inside that folder.
3. Write a clear message describing what you changed (not just "Add files via upload").

### Never upload
- `.env` or any API key: keys stay on Ahmed's machine and in Render's secret settings
- Big datasets (we link to them and credit them instead)

---

## Folder map

```
backend/        The server: FastAPI + Gemini + ElevenLabs (+ glossary.json)
frontend/       The app's screens
  voicebridge_FINAL.html   the whole frontend (one file)
  demo_audio/   pre-recorded demo lines (the demo uses no API credits)
  logo.svg      the logo
  old_mockup/   first Gemini Canvas design (credited, reference only)
tests/          How we tested it (start with tests/README.md)
  BASELINE_COMPARISON.md   ⭐ baseline vs VoiceBridge: results in one page
  evaluate_medical.py      the medical test script (11 languages)
  test_set_medical.csv     the 93 test sentences (from the 17 kept-aside consultations)
  results/medical/         medical test results (tables + examples)
  results/early_checks/    first checks while building (Urdu clip, voices in all languages)
  clips/recording/         native-speaker recordings, one folder per language
data/           PriMock57 split (40 build / 17 test), term counts (dataset itself: download from its GitHub)
docs/           Project brief, dev log, errors + fixes, frontend changes, explainer, write-up
  design/       the untouched AI-made original frontend (for comparison)
deploy/         how Render builds and runs the app (Dockerfile, requirements.txt)
```

## How VoiceBridge works (one turn)

```
Recording ─► audio.py ─────────► pipeline.py + prompts.py ─────────► voice.py ─────────► screen + speaker
             convert + noise      Gemini: speech-to-text, translate,    ElevenLabs speaks it
             check (refuse if     urgent symptoms, using our GP rules,  (Gemini voice as backup,
             too noisy)           glossary and conversation history     text-only after 15 s)
```
`sessions.py` remembers each appointment (access code, 20-turn limit, history), `service.py` joins the steps, and `main.py` exposes them as web addresses (`/api/...`). `ratelimit.py` stops spam.

## Running the backend locally (Windows, PowerShell)

First time only:
```
python -m venv .venv
.venv\Scripts\python -m pip install -r deploy/requirements.txt
notepad .env                  # create it with 3 lines: GEMINI_API_KEY=...  ELEVENLABS_API_KEY=...  ACCESS_CODE=...
```
Also needs **ffmpeg** installed (`winget install Gyan.FFmpeg`).

Start the server:
```
.venv\Scripts\python -X utf8 -m uvicorn backend.main:app --reload --port 8000
```
Then open **http://localhost:8000/docs** to test every endpoint in the browser (`POST /api/session` → `POST /api/turn` → `POST /api/summary` → `POST /api/end`).

Translate one file from the terminal, without the server:
```
.venv\Scripts\python -X utf8 -m backend.pipeline tests\clips\your_recording.m4a --from en --to ur
```

## Deploying
**Live app: https://voicebridge-hxyi.onrender.com** (access code: bridge2026). The home page's **Watch a demo consultation** button plays a scripted demo (Urdu or Arabic) with no access code and no API credits; **Start appointment** is always the real app.

The app runs on **Render** (free web service), built from this repo with `deploy/Dockerfile` (Render setting: Dockerfile Path = `./deploy/Dockerfile`). The keys go in Render's **Environment** settings, never in the code. On the free plan the app sleeps after 15 minutes without visitors, so the first visit then takes about a minute to load.
(We planned Hugging Face Spaces, but Docker Spaces now need a paid plan.)

**Updating the live app:** Render doesn't rebuild automatically (we deploy from the public repo link, not a GitHub connection). After pushing to `main`: Render dashboard → `voicebridge` → **Manual Deploy → Deploy latest commit**.

## Documentation
- `docs/DEV_LOG.md`: what we built, when, and **why** each decision was made
- `docs/ERRORS_AND_FIXES.md`: every error and fix, plus the **known issues and limitations** table
- `tests/README.md`: how the glossary was built and how we tested fairly
- `docs/PROJECT_BRIEF.md`: the full project brief and API contract

## Credits

| What | Used for | Link | Licence / terms |
|---|---|---|---|
| **Google Gemini API** (gemini-3.5-flash-lite; gemini-4-hydrogen for drafting the glossary; gemini-3.8-flash-lite-tts as backup voice) | Speech-to-text, translation, urgent-symptom detection, summaries, glossary drafts | https://ai.google.dev | Google Gemini API terms |
| **ElevenLabs** (eleven_v4_turbo, stock voices "Alice" and "Daniel") | Speaking the translations | https://elevenlabs.io | ElevenLabs terms (free plan) |
| **PriMock57**, Babylon Health (Papadopoulos Korfiatis et al., ACL 2022) | Glossary terms (40 consultations) and medical test sentences (17 held-out consultations) | https://github.com/babylonhealth/primock57 | CC BY 4.0 |
| **FLEURS**, Google | Real speech in our 11 languages for testing | https://huggingface.co/datasets/google/fleurs | CC BY 4.0 |
| **FLORES+** | Reference translations for testing | https://huggingface.co/datasets/openlanguagedata/flores_plus | CC BY-SA 4.0 |
| **SNOMED CT UK browser**, NHS | Checking official names of glossary terms | https://termbrowser.nhs.uk | Used for look-up only |
| **ONS Census 2021** | Choosing the 10 most common languages after English | https://www.ons.gov.uk | Open Government Licence |
| **FastAPI**, **Uvicorn**, **Pydantic** | Web server and API | https://fastapi.tiangolo.com | MIT / BSD |
| **pydub** + **ffmpeg** | Audio conversion and noise check | https://github.com/jiaaro/pydub · https://ffmpeg.org | MIT · LGPL/GPL |
| **python-dotenv**, **google-genai**, **elevenlabs** (Python SDKs) | Loading keys, calling the APIs | PyPI | BSD / Apache 2.0 / MIT |
| **Google Gemini Canvas** | First draft of the UI mockup (`frontend/old_mockup/`) | https://gemini.google.com | — |

*Every result in this repo comes from data not used to build the system, except where clearly marked as development data (FLEURS Urdu clips 1806 and 1930).*
