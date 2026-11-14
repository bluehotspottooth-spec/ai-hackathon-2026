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
- **Milestone 2 ✅:** Urdu and Polish doctor questions + an English patient sentence, generated in **0.6–1.1 s** each. Files: `tests/results/milestone2/`.
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

## Next
- A5: `sessions.py` (access code, 20-turn limit, stores each turn and passes the last 6 to `translate_audio(history=...)`).
- A6: `service.py` + `main.py`, the `/api` endpoints.
- Fetch the FLEURS English references once Hugging Face's service is back.
