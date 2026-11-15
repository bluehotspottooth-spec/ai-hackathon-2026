# VoiceBridge explained: everything you need for the judges

Plain English, no jargon you can't explain. Read it top to bottom once, then use the **judge questions** at the end to practise out loud.

Honesty note: Claude Code (an AI coding assistant) wrote much of the code with us. We decided what to build and why, tested it, and found and fixed the problems. Judges allow coding assistants as long as we credit them and **understand** the work, which is what this file is for.

---

## 1. The 30-second pitch

> "In the UK, millions of people don't speak English well, and GP appointments are short. Phone interpreters must be booked ahead and often aren't there. **VoiceBridge** is a voice translator built for the GP room. The doctor taps their button and speaks English; a few seconds later the patient **hears** it in their language (Urdu, Polish, Arabic, and 8 more) and **sees** it in big text. The patient replies the same way. On top of the AI we added a **medical glossary** from real-style GP consultations, a **GP-specific prompt** that never softens symptoms, **red urgent flags** for things like chest pain, and **safety warnings** when the audio is noisy or a word was unclear."

**One specific user:** a patient with limited English (for example an older Urdu-speaking woman) explaining her symptoms to a GP.

---

## 2. What happens when someone speaks (the journey of one sentence)

Learn this one. It explains the whole project.

1. **Tap the button and speak.** The browser records the microphone (a built-in browser feature called `MediaRecorder`). While recording, a ring of red sound bars moves with your voice, so you know it's hearing you.
2. **Tap again to send.** The page sends the recording to our server at `/api/turn`, with who spoke (doctor or patient).
3. **Clean-up and noise check** (`audio.py`). The server converts the audio to a standard format (WAV) using **ffmpeg**, then checks it: too short? silent? too noisy? It measures how much louder the speech is than the background. Very noisy → we refuse and ask them to repeat. A bit noisy → we translate but show a "Background noise" warning.
4. **Understand and translate** (`pipeline.py`). We send the audio to **Google Gemini** (model `gemini-3.5-flash-lite`) with **our GP prompt**, the **glossary** terms, and the **last few turns of the conversation** for context. Gemini returns a fixed set of fields (JSON): what was said, which language, the translation, urgent terms, unclear words, and how clear the speech was.
5. **Speak it** (`voice.py`). **ElevenLabs** turns the translation into speech (a different voice for the doctor's and the patient's words). If ElevenLabs fails, a **backup voice** (Gemini text-to-speech) tries, with a **15-second hard stop**. If both fail, the text still appears.
6. **Show it** (the frontend). The newest translation appears **big at the top** (the "spotlight"), with the original words underneath, any warnings, and the audio plays. Urgent terms appear in a **red banner** for the GP.
7. **Remember it** (`sessions.py`). The turn is saved in the server's memory so the next translation has context. When the appointment ends, **everything is deleted**.

It takes about **5 seconds** in total (we measured Urdu → English at 5.1 s and English → Urdu at 5.5 s).

---

## 3. The backend (Ahmed's part): one file at a time

The backend is the program on the server. It's written in **Python** using **FastAPI** (a library for making web APIs).

| File | What it does, simply | Why it matters |
|---|---|---|
| `main.py` | The "front door". Defines the web addresses (`/api/session`, `/api/turn`, `/api/summary`, `/api/end`) and also serves the website page. Also has a test page at `/docs` | One server does everything, so one link works on any phone |
| `service.py` | The "manager". Runs the steps of a turn in order (check, clean audio, translate, speak, save) and times each one | Logic is written once, in one place |
| `audio.py` | Converts any recording to WAV and checks it (too short, too long, silent, too noisy) | The AI **invented symptoms** when we gave it noisy audio, so we block bad audio before it reaches the AI |
| `pipeline.py` | Talks to Gemini: transcribe + translate in one call, structured output, 2 attempts, time limit | The core AI step |
| `prompts.py` | Our GP instructions to the AI, the 11 languages, and how the glossary is added | This is a big part of **our own work** on top of the AI |
| `glossary.json` | 106 medical terms from the PriMock57 GP consultations, with translations, marked verified or not, and which are urgent | Keeps medical words exact |
| `voice.py` | Text-to-speech: ElevenLabs first, Gemini backup, 15 s hard stop | The patient **hears** the answer, which matters if they can't read well |
| `sessions.py` | Keeps each appointment in memory: the language, the turns, a 20-turn limit, deleted after 2 hours or when ended | Privacy (nothing stored permanently) and protects our free API credits |
| `ratelimit.py` | Stops one person spamming the server (10 appointments an hour, 30 turns per 5 minutes) | Protects the public link |
| `errors.py` | Turns any error into a friendly message (`{"error": "..."}`) | Users never see scary code errors |

**Words you might be asked about:**
- **API**: a way for two programs to talk. Our page sends a request ("here's a recording") and gets an answer (the translation).
- **Endpoint**: one address on the API, like `/api/turn`.
- **JSON**: text in a fixed format of names and values, e.g. `{"translation": "I have chest pain"}`. Easy for programs to read.
- **Base64**: a way to turn sound (binary data) into plain text so it can travel inside JSON. The page turns it back into sound.
- **API key**: a secret password for Gemini and ElevenLabs. Ours are in a `.env` file that is **never** uploaded to GitHub (it's in `.gitignore`), and in Hugging Face "Secrets" when deployed.
- **Access code**: a password to start an appointment, so random people can't use up our credits. It's checked safely (`secrets.compare_digest`, which takes the same time whether the guess is close or not, so it can't be guessed letter by letter).

---

## 4. The frontend (the website): what we changed and why

The frontend is **one file**: `frontend/voicebridge_FINAL.html`. It holds three languages in one:
- **HTML** = the content and structure (headings, buttons, pages).
- **CSS** = the look (colours, sizes, layout, light and dark mode).
- **JavaScript** = the behaviour (recording, sending to the server, showing results, animations).

**Where it came from (be upfront about this):** an AI (Claude Code) made the first version, based on our earlier Gemini Canvas mockup. We kept that untouched (`docs/design/voicebridge_ORIGINAL.html`, Git tag `ai-original-mock`) and logged **every change we made** in `docs/FRONTEND_CHANGES.md`, with the reason. Judges can compare the two on GitHub.

### The pages
Home → How it works → Languages → Safety → About, plus the appointment flow: **access code → choose the language → the appointment → summary**. It's a "single-page app": all pages are in one file and JavaScript shows one at a time (the address bar changes, e.g. `#consult`, so the Back button still works).

### Our 11 changes, and the reasons to say out loud

| # | Change | How it works (simply) | Why (say this) |
|---|---|---|---|
| 1 | **Renamed files**: ORIGINAL vs FINAL | Just file names, plus a Git tag | Shows clearly what the AI made and what we made |
| 2 | **Logo**: two speech bubbles meeting | Drawn in SVG (shapes described as code, so it's sharp at any size) | The app is a bridge between two people's words |
| 3 | **Bigger, centred mic buttons** (88 px laptop, 72 px phone) | CSS sizes | It's the main thing people press; older or anxious patients need big targets |
| 4 | **Focus mode**: menu hidden during an appointment | When the page is on the appointment, CSS hides the menu | Nobody leaves the conversation by accident |
| 5 | **Quieter demo bar** | Smaller text, hidden on phones | The real buttons should stand out |
| 6 | **Simpler empty screen**: one instruction | Less text | First-time users see one thing to do |
| 7 | **Polish**: dot texture, soft shadows | CSS | Looks trustworthy |
| 8 | **Teal + apricot colours** | Colours are stored once as "tokens" (`--brand`, `--accent`) and used everywhere | Teal = calm and trust (health); one warm accent makes the main button obvious |
| 9 | **Animated home demo** (Urdu → Polish → Arabic) | JavaScript types the translation out letter by letter, on a loop. Turned off if the user's device asks for less motion | Shows what the app does in 5 seconds without reading |
| 10 | **Sound-wave ring while recording** | The browser's **Web Audio analyser** measures the mic's loudness 60 times a second, and we draw 48 bars on a `<canvas>` | Proof the app is hearing you, so people don't stop too early |
| 11 | **Live caption spotlight** | The newest translation shows big at the top; the previous one moves into an "Earlier in this appointment" list (newest first) | The phone sits **on the desk between two people**; the patient must read the latest sentence from across the desk |

### Safety features you can point at on screen
- **Red urgent banner** (e.g. "chest pain · shortness of breath"): stays at the top for the GP.
- **"Said in Urdu"**: the original words are always shown under the translation, so a bilingual person can check it.
- **Underlined unclear words**: the AI tells us which words it wasn't sure of.
- **"Background noise"** and **"Heard Polish, not Urdu"** badges.
- **"Not what I said"** button: asks the person to say it again.
- **Right-to-left text** for Urdu, Arabic and Persian (set automatically with the HTML `dir="rtl"` setting).
- **Demo mode** (`USE_MOCK = true`): scripted answers, so the demo works even without internet or credits. `false` = the real backend.

---

## 5. What makes it OUR work (not just "using Gemini")

Judges care most about this. Say these four things:

1. **Medical glossary from real data.** We took the **PriMock57** dataset (57 mock UK GP consultations). We split it: **40** to build the glossary, **17** held back for testing (random split, seed 2026), so we never test on what we built from. We extracted the most common medical terms (106), checked the English names, added translations, and marked each one **verified only if a native speaker checked it**.
2. **A GP-specific prompt.** Rules like: keep medical terms and doses exact; never soften or exaggerate symptoms (we caught it turning "tight pain" into "severe pain" and fixed it); flag urgent symptoms, but **not** when it's a question ("Do you have chest pain?") or a denial ("No chest pain").
3. **Safety layers around the AI.** The noise check (because it **invented symptoms** in noisy audio), unclear-word highlights, wrong-language warnings, retries, time limits, a backup voice.
4. **Testing against a baseline.** The `USE_MEDICAL_LAYER` switch turns our glossary and prompt off, so we can compare "plain Gemini" with "VoiceBridge", per language.

---

## 6. Honest limitations (judges reward honesty)

- **Not medical advice**, a prototype. Not approved for real clinical use.
- **Native-speaker checks are incomplete** for many languages; unverified glossary entries are only suggestions to the AI.
- **No real-phone testing yet** (needs the Hugging Face deployment).
- **Noise**: in heavy noise the AI can make things up; we block that, but a quiet room is needed.
- **Speed**: about 5 seconds a turn; sometimes slower if Gemini is busy. Our time limit doesn't fully cover a reply that arrives very slowly (a known fix we haven't done).
- **Sessions live in memory**: if the server restarts, the appointment is lost (fine for a prototype, and good for privacy).
- **Some FLEURS test data was missing** because Hugging Face had errors, so the general translation scores are incomplete.

---

## 7. Likely judge questions, with answers

**Q: What did you build yourselves, and what is the AI?**
A: Gemini does speech recognition and translation; ElevenLabs does the voice. We built everything around it: the medical glossary from PriMock57, the GP prompt, the urgent-term rules, the noise check, the safety warnings, the server, the website, and the testing against a baseline.

**Q: Why not just use Google Translate?**
A: Google Translate isn't built for a GP room: it doesn't flag urgent symptoms, doesn't warn about noise or unclear words, doesn't know GP vocabulary, and isn't a two-person conversation with both sides spoken. We also compare against a plain baseline to show what our layer adds.

**Q: How do you know it's accurate?**
A: We test on data **not used to build it** (the 17 held-out consultations, and FLEURS clips), per language, with a baseline, and with native-speaker checks where we have them. We show failures too.

**Q: What happens if the translation is wrong?**
A: The original words are always on screen, unclear words are underlined, there's a "Not what I said" button, and urgent symptoms are flagged separately. It's an aid, not a replacement for a professional interpreter in serious cases.

**Q: What about privacy?**
A: Nothing is saved to a database. The appointment lives in the server's memory and is deleted when it ends (or after 2 hours). API keys are never in the code.

**Q: Why these 11 languages?**
A: The 10 most common main languages in England and Wales after English (ONS Census 2021), plus Persian because a teammate speaks it.

**Q: Why does it take 5 seconds?**
A: Three steps: cleaning the audio (under 1 s), Gemini translating (2–3 s), and generating the voice (1–2 s). We chose the fastest Gemini model and the lowest "thinking" setting to keep it quick.

**Q: Why is the newest message big at the top?** (change #11)
A: In a real appointment the phone is on the desk between the GP and the patient. The patient needs to read the latest sentence from across the desk without scrolling through a chat, and bigger text helps older patients.

**Q: How does the sound wave work?**
A: The browser's Web Audio API gives us the loudness of different pitches from the microphone, many times a second. We draw that as 48 bars in a circle on a canvas. In demo mode we simulate a voice.

**Q: How would this work in a real GP surgery?**
A: It's a web link, so it works on any phone or computer with no install. Next steps would be native-speaker checks for every language, testing with real patients and GPs, and NHS data-protection approval.

**Q: What was the hardest problem?**
A: Good examples: the AI **invented symptoms** when the audio was noisy (we added the noise check); it raised urgent alerts when the doctor just **asked** about chest pain (we changed the rules); and it made "tight pain" into "severe pain" in the summary (we banned added intensity words). All logged in `docs/ERRORS_AND_FIXES.md`.

---

## 8. Where everything is (if a judge asks to see it)

- Code: `backend/` (server), `frontend/voicebridge_FINAL.html` (website)
- What we changed in the design: `docs/FRONTEND_CHANGES.md`
- Every error and how we fixed it: `docs/ERRORS_AND_FIXES.md`
- What we did each day: `docs/DEV_LOG.md`
- The project brief: `CLAUDE.md`
