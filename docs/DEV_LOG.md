# Development log (backend)

What we built, when, and **why we made each decision**. Problems and fixes are in [ERRORS_AND_FIXES.md](ERRORS_AND_FIXES.md).
All times are London time. Commit IDs link each entry to the GitHub history.

Built by Ahmed Khan with **Claude Code** (AI coding assistant), as allowed by the hackathon rules. Ahmed directs each step, tests it, and can explain every part.

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
- Downloaded 2 Urdu clips from **FLEURS** (Google, CC BY 4.0): test IDs 1806 and 1930. Results saved in `tests/results/milestone1_urdu.json`.
- **Speed:** 3–4 s per turn, fast enough for a live conversation.
- **Quality:** mixed, honestly reported:
  - Clip 1806 (12 s): transcribed almost perfectly in both modes. The baseline translated it correctly; VoiceBridge mistranslated one word ("pollution" → "flooding").
  - Clip 1930 (6 s): **both modes failed.** VoiceBridge wrote Hindi script and heard "Filipino… kidnapped" as "Afghan martyrs"; the baseline turned "released" into "burnt to death".
- **What we learned:** the medical layer is built for GP conversations, so general news sentences aren't a fair test of it. We still need the medical test (C3). Short clips and Urdu/Hindi confusion are real weaknesses.
- **Rule we're following:** these 2 clips are now "development data" and will be **left out** of the FLEURS evaluation.

---

## Next
- A3 follow-up: tell Gemini the exact script for each language (fix for the Hindi-script problem), then re-test on a **different** clip.
- A4: `voice.py`, text-to-speech with ElevenLabs.
