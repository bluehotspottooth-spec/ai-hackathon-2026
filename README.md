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
| `frontend/` | **UI teammate** | The web app people see. `frontend/mockup/` holds the original Gemini Canvas mockup |
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
frontend/       UI teammate: the app's screens
  mockup/       original Gemini Canvas design (credited)
tests/          Testing teammate: evaluation scripts
  clips/        test audio (not uploaded: too big / personal)
  results/      result CSVs and charts
data/           Testing teammate: datasets and term counts
docs/           Briefs, write-up (Submission for Hackathon.docx)
CLAUDE.md       Full project brief (single source of truth)
```

## Running the backend (Ahmed's machine)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      (then fill in the keys)
```

## Credits

Full credits list coming in the write-up. So far: Google Gemini (translation; Canvas for the UI mockup), ElevenLabs (speech), FastAPI, pydub, ffmpeg, Gradio, Claude Code (coding assistant).
