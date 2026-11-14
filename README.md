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
| `frontend/` | **Benet** | The web app people see: `index.html` (start with `frontend/README.md`). `frontend/old_mockup/` holds the OLD first Gemini Canvas mockup (reference only) |
| `tests/` and `data/` | **Testing teammate** | Glossary building, FLEURS + medical evaluations, results CSVs, charts |
| `docs/` | **Everyone** | Briefs and the write-up. Say in the team chat before editing a shared doc |
| Top level (`CLAUDE.md`, `requirements.txt`, `.gitignore`, `.env.example`) | **Ahmed** | Project setup. Ask Ahmed if you need a package added |

### Uploading through the GitHub website
1. Open **your** folder on GitHub first (e.g. click `frontend`).
2. Then **Add file → Upload files**. The files land inside that folder.
3. Write a clear message describing what you changed (not just "Add files via upload").

### Never upload
- `.env` or any API key: keys stay on Ahmed's machine and in Hugging Face Secrets
- Big datasets (we link to them and credit them instead)

---

## Folder map

```
backend/        Ahmed: FastAPI + Gemini + ElevenLabs
frontend/       Benet: the app's screens (index.html + README.md)
  index.html    NEW MOCK (v2): the current design
  old_mockup/   OLD first Gemini Canvas design (credited, reference only)
tests/          Testing teammate: evaluation scripts
  clips/        test audio (not uploaded: too big / personal)
  results/      result CSVs and charts
data/           Testing teammate: datasets and term counts
docs/           Briefs, write-up (Submission for Hackathon.docx), dev log, errors + known issues
CLAUDE.md       Full project brief (single source of truth)
Dockerfile      Recipe for running the app on Hugging Face (later)
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
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env        # then fill in GEMINI_API_KEY, ELEVENLABS_API_KEY, ACCESS_CODE
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

## Deploying (later)
`Dockerfile` is ready for a Hugging Face **Docker Space** (port 7860). The keys go in the Space's **Settings → Secrets**, never in the code.

## Documentation
- `docs/DEV_LOG.md`: what we built, when, and **why** each decision was made
- `docs/ERRORS_AND_FIXES.md`: every error and fix, plus the **known issues and limitations** table
- `docs/DATASET_CHECKING_PLAN.md`: how the glossary was built and how we test fairly
- `CLAUDE.md`: the full project brief and API contract

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
| **Gradio** | (Optional frontend) | https://gradio.app | Apache 2.0 |
| **Google Gemini Canvas** | First draft of the UI mockup (`frontend/old_mockup/`) | https://gemini.google.com | — |
| **Claude Code** (Anthropic) | AI coding assistant used to write and test the backend with Ahmed | https://claude.com/claude-code | — |

*Every result in this repo comes from data not used to build the system, except where clearly marked as development data (FLEURS Urdu clips 1806 and 1930).*
