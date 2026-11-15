# 👋 For Benet: VoiceBridge frontend, start here (NEW MOCK v2)

**Owner of this folder: Benet** (frontend). Backend questions: ask Ahmed.

| File | What it is |
|---|---|
| **`index.html`** | ✅ **NEW MOCK (v2)**: the current design. Work on this one |
| **`README.md`** | ✅ **NEW MOCK (v2)**: this guide |
| `old_mockup/` | ❌ The OLD first mockup from Gemini Canvas. Reference only, don't edit |

> **Team decision (15 Nov):** this mock is our main frontend. The AI-made original stays untouched in `docs/design/` (Git tag `ai-original-mock`). **Write down every change you make, and why, in [`docs/FRONTEND_CHANGES.md`](../docs/FRONTEND_CHANGES.md).** That's our evidence of what we added ourselves.

`frontend/index.html` is the **whole frontend in one file** (HTML + CSS + JavaScript). It's the clickable prototype, already wired to our backend. Your job: **make it yours** (small design changes, wording, polish), **then switch it to the real backend** and test it with a real microphone.

> Live demo of the same design (Ahmed can share it): a private claude.ai link from the team.
> First draft of this design was AI-generated (Claude Code, based on the earlier Gemini Canvas mockup in `old_mockup/`). Credit both in the write-up.

---

## 1. See it working (2 minutes, no backend needed)

Double-click `frontend/index.html` (or in PowerShell, from the `voicebridge` folder: `start frontend\index.html`).

It opens in **demo mode** (`USE_MOCK = true`): scripted answers, no microphone, no server.
- Any access code works (type `wrong` to see the error)
- On the appointment screen, **tap** a mic button to start and tap again to send, or press **Play the whole demo**

---

## 2. What you CAN change freely ✅

| What | Where in `index.html` |
|---|---|
| **Colours** (light and dark) | The `:root { --bg: ...; --brand: ...}` block at the top of `<style>`. Change a colour once there and it changes everywhere. Dark mode colours are in the two blocks just below it |
| **Fonts** | `--font` and `--display` in `:root`, plus the Google Fonts `<link>` |
| **Wording** (headlines, buttons, page text) | The HTML inside each `<section class="view" id="v-...">` |
| **Layout and spacing** of the info pages (Home, How it works, Languages, Safety, About) | Their HTML and CSS |
| **Icons** | The `<symbol id="i-...">` list near the top of `<body>` (line icons) |
| **Demo conversation** | `const SCRIPT = [...]` in the script |
| **Hints in each language** ("Hold to speak") | `const LANGS = [...]`: `hint`, `word`, `phrase` (please get native speakers to check these!) |

## 3. What you must NOT change ❌ (or it won't connect to the backend)

1. **The `realApi` object** in the script: the addresses `/api/session`, `/api/turn`, `/api/summary`, `/api/end` and the field names `access_code`, `doctor_lang`, `patient_lang`, `session_id`, `speaker`, `audio`. These must match the backend exactly (see `CLAUDE.md` section 6).
2. **The field names the page reads back:** `original_text`, `translation`, `detected_language`, `target_language`, `urgent_terms`, `unclear_words`, `speech_clarity`, `noisy`, `audio_base64`, `timings`, `turns_left`, `summary_en`, `summary_patient_lang`.
3. **Element `id`s that the script uses** (e.g. `btn-doctor`, `btn-patient`, `thread`, `turns`, `urgent-banner`, `access-form`, `lang-grid`, `sum-en`, `sum-pat`, `end-modal`). Rename one → also rename it in the script, or it breaks. If unsure, search the file for `$("the-id")`.
4. **The safety displays:** urgent banner, "Said in …" original text, underlined unclear words, noise and wrong-language badges, "Not what I said". These are part of our safety story for the judges.
5. The footer line **"This project is a prototype and is not medical advice."**

Tip: after each change, reload the page and run **Play the whole demo**. If the demo still works, you haven't broken anything.

---

## 4. Connect it to the real backend (about 30 minutes)

Already tested by Ahmed and Claude: with `USE_MOCK = false` it worked first time with the real backend (session, Urdu → English and English → Urdu turns in about 5 s each with spoken audio, urgent banner, summary, appointment deleted at the end).

1. Get the latest code: `git pull`
2. In `index.html`, find `const USE_MOCK = true;` and change it to **`false`**
3. Ahmed (or you, with the `.env` keys) starts the backend from the `voicebridge` folder:
   ```
   .venv\Scripts\python -X utf8 -m uvicorn backend.main:app --reload --port 8000
   ```
4. Open **http://localhost:8000** in **Chrome** (not by double-clicking the file: the real API only works through the server)
5. Enter the real access code (from Ahmed's `.env`), pick a language, allow the microphone, and talk

**Microphone rules:** it only works on `http://localhost` or an `https://` site. Phones need the deployed Hugging Face link, so phone testing comes after deployment.

### Checklist once connected
- [ ] Wrong code shows the error; right code starts an appointment
- [ ] Doctor speaks English → Urdu text appears **and is spoken**
- [ ] Patient speaks → English text appears and is spoken
- [ ] Saying "I have chest pain" shows the red urgent banner; "Do you have chest pain?" does **not**
- [ ] A noisy room gives the noise message or badge
- [ ] Replay button plays the audio again
- [ ] End → summary in both languages
- [ ] Works in Chrome on a laptop; after deployment, works on an iPhone and an Android phone

### Time estimate
| Step | Time |
|---|---|
| Your design tweaks | as long as you want (keep it to 1–2 h: feature freeze is **Sunday 1 PM**) |
| Flip `USE_MOCK`, run, first real turn | 10–15 min |
| Test all the checklist items on a laptop | 20–30 min |
| Phone testing after deployment (iPhone audio can need a tap) | 30–60 min |

The starting version is already committed (by Ahmed), so every change you commit after this shows up as **your** work in the history. Judges like to see who did what, so commit often with clear messages (e.g. "Change colours to …", "Fix phone layout of …").
