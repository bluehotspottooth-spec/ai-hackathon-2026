# Development log (backend)

What we built, when, and **why we made each decision**. Problems and fixes are in [ERRORS_AND_FIXES.md](ERRORS_AND_FIXES.md).
All times are London time. Commit IDs link each entry to the GitHub history.

Built by Ahmed Khan. Tools and services used are credited in the README and the write-up.

---

## Saturday 14 November 2026

### 10:46 · A1: project setup · `4839e2e`
- Created the folder structure, `.gitignore`, `.env.example`, a virtual environment and `requirements.txt`.
- **Decision: pin exact package versions** (e.g. `gradio==6.32.0`) so the Hugging Face server installs exactly what we tested.
- **Decision: API keys live only in `.env`**, which Git never uploads. The repo is safe to make public.
- Set up keys: Gemini (works) and ElevenLabs (free plan, 10,000 credits/month; key restricted to text-to-speech, voices, models and user info).

### 10:59 · A2: audio conversion (`backend/audio.py`) · `3772c5e`
- Converts any recording (Chrome webm, iPhone m4a, mp3, Gradio wav, Android ogg) to **16 kHz mono WAV**.
- Rejects empty, unreadable, too short (< 0.5 s), too long (> 60 s) and silent recordings **before** spending money on an API call.
- **Decision: 16 kHz mono** is standard for speech and keeps files small (~32 KB per second).
- **Tested:** 10 generated clips. All 5 formats converted, all 5 bad clips rejected with a friendly message.

### 11:25 · Joined the team GitHub repo · `2fc3852`
- Merged our local work with the team repo (README, UI briefs, Word write-up, UI mockup).

### 11:29 · Organised the repo by person · `8a1fea4`
- `backend/` = Ahmed, `frontend/` = UI teammate, `tests/` + `data/` = testing teammate, `docs/` = shared.
- **Decision:** one owner per folder, so nobody overwrites anyone else's work.

### 11:43 · A3 part 1: Gemini translation (`backend/prompts.py`, `backend/pipeline.py`) · `5c28348`
- `translate_audio()` sends one recording to Gemini and gets back the **transcript, detected language, translation and urgent symptoms in one call**.
- **Decision: one call, not two** (speech-to-text then translate): less waiting, and Gemini hears the speech while translating.
- **Decision: structured JSON output.** Gemini fills in a fixed 4-field "form", so our code never has to dig the answer out of free text.
- **Decision: two prompt versions.** The *baseline* is a plain "transcribe and translate". *VoiceBridge* adds our GP interpreter rules (keep negations, doses and first person; never soften symptoms; never add advice), 13 urgent symptoms, and a slot for the glossary. A `USE_MEDICAL_LAYER` switch lets tests compare the two.
- **Decision: model = gemini-3.5-flash-lite.** We benchmarked 4 models. The newest (gemini-4-hydrogen) took 56–135 s per turn, Flash-Lite took 4 s with the same urgent flags, and a live conversation needs seconds.
- **Tested (English → Urdu, robot voice):** correct Urdu; flagged "chest pain" and "shortness of breath"; did **not** flag "I do not have a fever"; kept "500 mg twice a day" exact.

### ~12:00 · Milestone 1: real Urdu speech → English
- Downloaded 2 Urdu clips from **FLEURS** (Google, CC BY 4.0): test IDs 1806 and 1930. Results saved in `tests/results/early_checks/milestone1_urdu.json`.
- **Speed:** 3–4 s per turn, fast enough for a live conversation.
- **Quality:** mixed, honestly reported:
  - Clip 1806 (12 s): transcribed almost perfectly in both modes. The baseline translated it correctly; VoiceBridge mistranslated one word ("pollution" → "flooding").
  - Clip 1930 (6 s): **both modes failed.** VoiceBridge wrote Hindi script and heard "Filipino… kidnapped" as "Afghan martyrs"; the baseline turned "released" into "burnt to death".
- **What we learned:** the medical layer is built for GP conversations, so general news sentences aren't a fair test of it. We still need the medical test (C3). Short clips and Urdu/Hindi confusion are real weaknesses.
- **Rule we're following:** these 2 clips are now "development data" and will be **left out** of the FLEURS evaluation.

### ~12:30 · Script fix + conversation history (`prompts.py`, `pipeline.py`)
- **Script fix:** a `SCRIPTS` table tells Gemini exactly which writing system to use for each language (e.g. Urdu = Perso-Arabic, never Hindi script). Result on the 2 dev clips (3 runs each): Urdu script **6/6** (before: Hindi/Roman), and "pollution" now correct 3/3. The "burnt to death" mis-hearing remains (see ERRORS_AND_FIXES #14).
- **New feature: conversation history (context).** Each turn can now include the **last 6 turns** of the appointment as context, so Gemini knows what "it" or "the left side" refers to.
  - **Decision: history lives in the backend**, not the frontend: the session (A5) keeps the turns and passes them in. The frontend doesn't change, and the history is deleted when the appointment ends.
  - **Decision: send text, not old audio.** The previous transcripts and translations are enough context, and resending old audio would make every turn slower.
  - **Decision: 6 turns** (about 3 question-and-answer pairs): enough to know the topic, small enough to stay fast.
  - **Safety rule in the prompt:** history is *for understanding only*. Don't re-translate it, and don't add anything the speaker didn't say.
  - **Decision: the baseline gets no history**, so tests can measure what our layer adds.
- **Tested:** patient says *"I have a very bad cough"*, doctor asks *"When did the cough start?"*, then the English clip *"It started two days ago…"* is translated to Urdu. In Urdu the verb must agree with the noun's gender; *cough* (کھانسی) is feminine.

  | | Verb form | Correct? |
  |---|---|---|
  | No history (3 runs) | شروع ہوا (masculine) | ❌ 0/3 |
  | **With history** (3 runs) | **شروع ہوئی** (feminine, agrees with "cough") | ✅ 3/3 |

  Same speed (2.4–3.3 s), and it still said "it", without adding the word "cough".

### ~13:15 · A4: speech (`backend/voice.py`) + Milestone 2
- `speak(text, language, speaker)` turns the translation into MP3 audio with ElevenLabs.
- **Decision: model `eleven_v4_turbo`.** It's the only fast model that supports all 11 languages. The older models used in most tutorials skip Urdu, Panjabi, Bengali, Gujarati and Persian.
- **Decision: two stock British voices**: *Alice* speaks the patient's words (in English) to the doctor, and *Daniel* speaks the doctor's words to the patient. Different voices make the direction obvious. They're stock voices, so we're not using anyone's real voice.
- **Decision: send the language code** with the text, because Urdu, Persian and Arabic share an alphabet; the code tells the voice how to pronounce it.
- **Milestone 2 ✅:** Urdu and Polish doctor questions + an English patient sentence, generated in **0.6–1.1 s** each. Files: `tests/results/early_checks/milestone2/`.
- **All-languages check:** we spoke one GP sentence in all 11 languages and had Gemini listen back: right language 11/11, 95–100% word match. It caught two real problems (Polish slash read aloud, Arabic letter), both fixed and re-tested (ERRORS_AND_FIXES #19–21).
- **Cost:** about **0.4 credits per character**. 9,643 credits left = roughly 400 more spoken turns this month, so testers should avoid big speech batches.

### ~14:30 · Safety features + backup voice
*(All problems, test numbers and open issues for this step are in [ERRORS_AND_FIXES.md](ERRORS_AND_FIXES.md) #22–29 and the Known Issues table K1–K16. This log only lists what was built and why.)*
- **Noise check (`audio.py`):** measures speech-vs-background contrast with plain maths. Too noisy (< 4 dB) → ask to repeat; noisy (< 12 dB) → translate with a warning. **Why:** in heavy noise the AI invented symptoms that were never said; an objective check doesn't depend on the AI being honest.
- **"Never invent" rule + `speech_clarity`** (clear / partly_unclear / inaudible) in the prompt and the JSON form. **Why:** a made-up symptom is more dangerous than "please repeat".
- **`unclear_words`:** Gemini lists words it's unsure of, for highlighting. **Why:** it was asked for, and costs nothing. In tests the AI rarely admits doubt, so it's never the only safety check.
- **Automatic retry + 20 s time limit** on translation. **Why:** temporary failures and random slow answers (up to 54 s) shouldn't ruin a turn.
- **Backup voice (Gemini TTS):** used automatically if ElevenLabs fails. **Why:** the free ElevenLabs credits could run out before the demo. Works in all 11 languages, including Urdu.
- **API contract updated** (approved by Ahmed): `/api/turn` now also returns `unclear_words`, `speech_clarity` and `noisy`. Both UI briefs explain how to show them ("Is that what you said?").

### ~15:00 · Backup-voice hard stop + dataset checking plan
- **Backup voice hard stop:** if Google's voice hasn't answered in 15 s, the turn returns text only (details: ERRORS_AND_FIXES #28).
- **`docs/DATASET_CHECKING_PLAN.md`:** how the testing teammate builds the glossary and tests fairly.
  - **Decision: ~80–100 glossary terms, chosen by category** (frequent PriMock57 words, NHS red-flag symptoms, common UK GP medicines, words the baseline gets wrong) rather than just "the 40 most frequent". **Why:** more safety coverage, but still few enough to translate into 11 languages and check.
  - **Decision: every English term checked against SNOMED CT** (the NHS's official vocabulary), recording its ID.
  - **Decision: PriMock57 split 40 build / 17 test with a fixed random seed**, saved in `data/split.json`. **Why:** results must come from data not used to build the system.
  - Licences checked: PriMock57 CC BY 4.0, FLEURS CC BY 4.0, FLORES+ CC BY-SA 4.0.

---

### ~15:30 · C1: glossary built from PriMock57 (in the testing folder)
- Downloaded the **PriMock57 transcripts** (114 TextGrid files, 1.7 MB, CC BY 4.0; no audio) into `data/primock57/` (not uploaded to GitHub).
- `tests/primock57.py` reads them: it merges doctor + patient files into one conversation and removes transcriber tags.
- `tests/build_glossary.py`:
  - `split`: **40 BUILD / 17 TEST**, shuffled with fixed seed 2026 → `data/split.json`.
  - `extract`: Gemini listed the medical terms in each of the 40 BUILD consultations → **388 different terms**, counted by how many consultations mention them → `data/term_counts.csv`. Top: fever (24), nausea (20), vomiting (18), paracetamol (16), diarrhoea (15), headache (15).
  - `build`: chose **106 terms** (48 frequent clinical terms, 35 medicines, 23 NHS urgent warning signs) and drafted **1,166 translations** into all 11 languages → `backend/glossary.json`. Automatic check (script, slashes, gaps): 0 problems.
  - **Decision: a stronger model (gemini-4-hydrogen) drafts the glossary.** It runs once, offline, so quality matters more than speed (the live app keeps the fast model).
  - **Decision: `verified=false` everywhere and SNOMED IDs left empty.** Only a real speaker can verify a translation, and only a person should confirm an NHS code.
- `tests/make_medical_test_set.py`: **93 sentences** (51 doctor, 42 patient) containing glossary terms, **only from the 17 TEST consultations** → `tests/test_set_medical.csv` (input for C3).
- Translation time limit lowered from 20 s to 12 s after one 36 s turn (normal turns: 3–4 s, with or without the glossary).

### ~15:45 · A5 + A6: sessions, service and the API (Milestone 3)
- `backend/sessions.py`: the access code (compared safely with `secrets.compare_digest`), the 20-turn limit (only successful turns count), stored turns that feed the **conversation history**, and appointments deleted on "end" or after 2 hours. **Decision: in memory, not a database.** Simpler, and nothing is kept after the appointment, which is good for privacy.
- `backend/errors.py`: one `ServiceError` (friendly message + HTTP status) used everywhere.
- `backend/service.py`: the 4 functions both frontends use. One turn = noise check → translate with history → speak (with backup) → save. Also the **summary** (A7): English + patient language, only what was said, urgent symptoms highlighted.
- `backend/main.py`: FastAPI endpoints `/api/session`, `/api/turn`, `/api/summary`, `/api/end`, `/api/health`; errors always come back as `{"error": ...}`; a 10 MB upload limit; serves `frontend/index.html` when it exists, otherwise `/` goes to the `/docs` test page.
- **Milestone 3 ✅:** a full appointment over HTTP. Wrong code 401; Urdu patient turn **4.2 s**; English doctor turn **5.5 s** (with urgent flags); noisy turn refused (400); summary in both languages; end; using it after ending → 404.
- **Glossary connected:** checked translations are given as rules, AI-drafted ones as suggestions; glossary urgent terms join the urgent list.

### ~16:30 · Spam protection, Dockerfile prepared, README + credits
- **`backend/ratelimit.py`:** per visitor (IP address), max **10 new appointments per hour** and **30 turns per 5 minutes**, otherwise 429 "Too many requests, please wait". **Why:** once the app is public, one person could burn our ~400 monthly spoken turns of ElevenLabs credits. A real appointment never gets near these limits. **Tested** with FastAPI's test client (no AI calls): the 11th appointment and the 31st turn were refused, and everything else kept working.
- **`Dockerfile` + `.dockerignore` prepared, NOT deployed.** **Decision (Ahmed): don't publish the backend on its own.** Without the frontend there's nothing useful for users to see, so we deploy once the frontend is ready. The Dockerfile installs Python 3.12 + ffmpeg, runs as a normal user, listens on port 7860 (Hugging Face's standard), and takes keys from Space Secrets, never from a file. **Not build-tested** (Docker isn't installed locally), but a simulation with only the files Docker copies (`backend/` + `frontend/`, keys as environment variables) started, created a session and loaded all 106 glossary terms.
- **README:** how one turn works, how to run and test locally (`/docs`), and the **full credits table** (APIs, datasets, libraries, AI tools, with links and licences).

### ~18:00 · Premium design proposal (`docs/design/voicebridge_premium_mockup.html`)
- On Ahmed's request: a sleeker, clickable redesign of the frontend that matches the backend's API exactly. It runs in **demo mode** (a scripted Urdu consultation) and switches to the real API with `USE_MOCK = false`.
- **Design decisions:**
  - **One layout for laptop and phone:** the conversation as chat bubbles in the middle, and a **bottom dock with two big hold-to-speak buttons**. This fixes the phone problem found in the mockup test (the mic bar squashed the text and covered "End appointment").
  - **The translation is the big text** in each bubble (it's what the *listener* reads); the original is smaller underneath.
  - A **pinned urgent banner** that doesn't scroll away; **live sound bars** while recording; **"Translating" dots**.
  - **Real line icons instead of emojis**; the **Atkinson Hyperlegible** font (designed by the Braille Institute for readability); a calm palette (ink, teal, warm off-white); **no NHS branding**.
  - **The patient's button hint is in their own language** (e.g. Urdu: بولنے کے لیے دبائے رکھیں). These 11 hints are AI-translated and not yet checked by native speakers.
- **Checked in the browser** at laptop (1024 px) and phone (375 px) sizes: welcome → wrong code → language search → appointment (5 turns: urgent banner, unclear-word highlight, background-noise badge, too-short press) → summary. No sideways scrolling on phones. Two layout bugs were fixed along the way (the speak-button text ran onto one line; the demo label covered the End button).

### ~19:00 · Prototype v2: multi-page and fully clickable (same file, replaces v1)
- Ahmed couldn't interact with v1: you had to *hold* the mic buttons, so a normal click seemed to do nothing. v2 changes:
  - **Multiple pages** with a menu: Home, How it works, Languages, Safety, About, plus the appointment flow (Start → Language → Appointment → Summary). Each page has its own link (`#how`, `#languages`…), and the browser's Back button works.
  - **Tap or hold to talk:** tap once to start and again to send, or hold and release. Keyboard: Space or Enter.
  - **"Play the whole demo"** runs a 6-turn scripted Urdu consultation by itself, and **"Watch a demo consultation"** on the home page starts it straight away. The demo can read translations aloud with the browser's own voice (a preview only; the real app uses ElevenLabs).
  - **Languages page:** every language with its script, direction, census rank and a "Where does it hurt?" phrase you can play (phrases AI-drafted, to be checked).
  - **Safety page** uses our real test results (invented symptoms 2/2 → 0/4) and an honest "known limits" list.
  - A **light and dark theme**, and an in-page "End this appointment?" confirmation (published pages block the browser's pop-up box).
- **Tested with real clicks and typing** in the browser: menu pages, code entry, language choice, tap-to-talk, the full automatic demo, End → summary, and phone layout (no sideways scrolling). Bugs found and fixed: the end box showed on load (`hidden` was overridden), menu links didn't switch pages in the preview (page switching now runs through JavaScript), the demo bar layout, and the button dock floating mid-screen.
- **Published as a private online preview link** for the team to click through (shared from its Share menu). The file in `docs/design/` is the same page and still works locally or as `frontend/index.html` with `USE_MOCK = false`.

### ~19:40 · Frontend handed over + connection tested
- **`frontend/index.html`:** the prototype is now the frontend's starting point (demo mode on). The UI teammate builds on top of it.
- **`frontend/README.md`:** a handoff guide: what's safe to change (colours, fonts, wording, layout of the info pages), what must stay (API calls and field names, element ids, safety displays, disclaimer), how to connect (`USE_MOCK = false`, open `http://localhost:8000`), a checklist and time estimates.
- **Connection tested end to end** (temporary copy with `USE_MOCK = false`, served by the backend): real session, Urdu → English turn **5.1 s** and English → Urdu turn **5.5 s** with spoken audio, urgent banner, summary in both languages, and the appointment deleted afterwards (turn after ending → 404). **No code changes were needed to connect.** Not tested: a real microphone (the test browser blocks it) and phones.
- Two backend prompt fixes verified or added along the way: questions no longer raise urgent alerts, and the summary no longer adds "severe" (ERRORS_AND_FIXES #35, #36).

## Sunday 15 November 2026

### ~13:20 · Team decision: the new mock is our frontend
- **Decision (team):** the NEW MOCK (v2) becomes the main frontend. Benet refines it (layout, mic button size, visual polish, a logo), and then it's connected to the backend and deployed.
- **How we keep it honest:** the AI-generated original stays untouched in `docs/design/voicebridge_premium_mockup.html` and is bookmarked with the Git tag **`ai-original-mock`**. Every team change goes into **`docs/FRONTEND_CHANGES.md`** (what, why, who, commit), and the GitHub compare view shows the exact difference.

### Afternoon · Frontend made clearer (changes #1–#11 in FRONTEND_CHANGES.md)
- Files renamed to `voicebridge_ORIGINAL.html` (AI original, in `docs/design/`) and `frontend/voicebridge_FINAL.html` (ours); the backend serves FINAL at `/`.
- Logo, bigger centred mic buttons, focus mode, new teal + apricot colours, an animated home demo, a sound-wave ring while recording.
- **Live caption spotlight (#11):** the newest translation is shown big at the top, older ones in an "Earlier in this appointment" list. **Why:** the phone sits on the desk between the GP and the patient, so the latest sentence must be readable from across the desk. Tested with the full demo at laptop and phone size.

### Afternoon · Optional voice cloning added (after feature freeze, team decision)
- **What:** with consent, a speaker records 10-45 s; ElevenLabs **Instant Voice Cloning** makes a temporary copy of their voice, and their translated words are spoken in their own voice.
- **Backend:** `voice.py` (`clone_voice`, `delete_voice`, `delete_leftover_clones`), `service.py` (`clone_voice`: consent, at least 10 s, not noisy), `main.py` (`POST /api/clone`, exactly as in the API contract), `ratelimit.py` (6 clones an hour). If a cloned voice fails mid-appointment, the stock voice takes over, then the backup voice.
- **Privacy:** clones are deleted when the appointment **ends**, when it **expires** (2 h), and any **leftovers at server start-up**. We only delete voices named "VoiceBridge temp…", never other voices on the account. **Team voices only**, consent box required (nothing is recorded without it).
- **Frontend:** change #12 in FRONTEND_CHANGES.md ("Use your own voice (optional)" pop-up).
- **Tested:** demo mode at laptop and phone size; backend: no consent, too-short sample, ending. **Not yet:** a real clone, because the API key needs the "Voices: write" permission and the Starter plan (ERRORS_AND_FIXES #37).
- **Later:** Ahmed upgraded to ElevenLabs Starter and gave the key "Voices: write". Fixed a library bug (#39); clone creation (2.6 s) and deletion now verified. Speaking with a clone of a *stock* voice was blocked by ElevenLabs' anti-misuse check (#40), so the final check needed a team member's own voice. **Real test passed (Ahmed's voice, with consent, real app in Chrome at localhost):** clone → 2 turns spoken in his own voice → summary → End → 0 clones left on the account. This was also our first real-microphone test of the full frontend. Added "Your voice is not kept" to the Home page warning (FRONTEND_CHANGES #13).
- **Why a decision was needed:** the brief's feature freeze was Sun 1 PM. The team chose to add it because it's listed as optional in the brief and the API contract already had `/api/clone`.

### Evening · Deployed on Render (Milestone 5, laptop part)
- **Live link: https://voicebridge-hxyi.onrender.com**
- **Why Render, not Hugging Face:** Hugging Face Docker Spaces now need the paid PRO plan ($9/month); Render's free plan runs our Dockerfile at no cost. Trade-off: it sleeps after 15 min idle (~1 min to wake). (ERRORS_AND_FIXES #41)
- **Steps:** the page now picks demo/real mode by itself; the Dockerfile uses Render's `PORT`; the repo was made public by its owner (no keys in the history, checked); Render web service created from the public repo (Docker, Frankfurt, free plan, health check `/api/health`); Ahmed typed the 3 secret values into Render's Environment Variables himself.
- **Tested live:** wrong code refused, a full English → Urdu turn with urgent flags and audio in 10.2 s, appointment deleted. **Still to test:** phones (iPhone + Android), the voice cloning flow online.

---

## Next
- Benet: design tweaks to `frontend/voicebridge_FINAL.html`, then test with a real microphone in Chrome (`USE_MOCK = false`).
- Deploy to Hugging Face once the frontend is ready (Ahmed: make an HF account and Space; add 3 secrets).
- Evaluation scripts (C2 FLEURS, C3 medical baseline vs VoiceBridge).
- Fetch the FLEURS English references once Hugging Face's service is back.
