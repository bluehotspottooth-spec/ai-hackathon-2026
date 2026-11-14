# VoiceBridge: UI / frontend brief

This is the frontend part of our hackathon project. It is meant to be read on its own, so you don't need the full project brief. If you're using Claude Code (or another AI assistant), give it this whole file first and tell it to follow the "Rules" section.

> **Deadline:** feature freeze **Sunday 1 PM** (London). We submit Sunday evening.
> **Your folder:** `frontend/` only (`index.html`, `styles.css`, `app.js`). The backend (Malik) is built separately and joins up through the API below.

---

## 1. What we're building (30-second version)

**VoiceBridge** is a live voice translator for **GP appointments in the UK**.

- **User:** a patient with limited English who needs to explain their symptoms to a GP and understand what the GP says back.
- A doctor and a patient share **one screen** (laptop or phone on the desk).
- One person **holds a mic button and speaks**. When they let go, the audio goes to our server. A few seconds later the other person **hears the translation spoken aloud**, and a **two-language transcript** appears on screen.
- Urgent symptoms (e.g. "chest pain", "can't breathe") show up as a **red flag for the doctor**.

The UI should feel **calm, trustworthy and medical**: like an NHS app, not a game.

---

## 2. Rules (for you and your AI assistant)

1. **Plain HTML + CSS + JavaScript.** No React, no build tools, no npm. Three files: `index.html`, `styles.css`, `app.js`. The backend serves them as static files.
2. Work in **small steps**: build one thing, check it in the browser, then move on.
3. Make sure you can **explain every part** yourself, because judges will ask questions live.
4. **No API keys in the frontend, ever.** The browser only talks to *our* backend (`/api/...`), never to Gemini or ElevenLabs directly.
5. **Don't change the API contract (section 4)** without agreeing it with Malik first.
6. All code must be written **during the hackathon** (from Sat 14 Nov 5:00 AM London). Commit often so the history shows this.
7. **Credit everything** you use (fonts, icons, snippets) in a list we can paste into the write-up, with a link and licence for each.
8. Simple, readable code with short comments beats clever code.

---

## 3. Screens

It's a single page, but only one screen is visible at a time. Use 4 `<section>`s and show/hide them with JS.

### Screen 1: Access
- App name + one-line tagline (e.g. "Speak to your GP in your own language").
- Access code input + "Start" button → `POST /api/session` (see section 4). Only send `access_code` here; the languages come from Screen 2. **Suggestion:** collect the code here, then call `/api/session` once at the end of Screen 2 with all three fields. Agree this with Malik.
- Wrong code → friendly inline error ("That code didn't work. Check with the clinic staff.").

### Screen 2: Setup
- "Which language does the patient speak?" with a grid of **11 large buttons**, showing the native name first:

| Code | Button label | Direction |
|---|---|---|
| `pl` | Polski · Polish | LTR |
| `ro` | Română · Romanian | LTR |
| `pa` | ਪੰਜਾਬੀ · Panjabi | LTR |
| `ur` | اردو · Urdu | **RTL** |
| `pt` | Português · Portuguese | LTR |
| `es` | Español · Spanish | LTR |
| `ar` | العربية · Arabic | **RTL** |
| `bn` | বাংলা · Bengali | LTR |
| `gu` | ગુજરાતી · Gujarati | LTR |
| `it` | Italiano · Italian | LTR |
| `fa` | فارسی · Persian | **RTL** |

- Doctor is always English (`en`). Show this as fixed text, not a choice.
- "Begin appointment" button.
- *(Optional, only if we enable voice cloning later: a consent checkbox + record-a-sample step. **Don't build this now**, but leave room for it.)*

### Screen 3: Appointment (the main screen)

**Desktop layout (3 columns):**
```
┌──────────────┬──────────────────────────┬──────────────┐
│ DOCTOR       │   SHARED TRANSCRIPT      │ PATIENT      │
│ English      │   (scrolls, newest at    │ اردو Urdu    │
│              │    bottom)               │              │
│   ( 🎤 )     │   [card] [card] [card]   │   ( 🎤 )     │
│ hold to speak│                          │ hold to speak│
│ status text  │                          │ status text  │
└──────────────┴──────────────────────────┴──────────────┘
  Turns left: 17                         [End appointment]
```

**Phone layout:** stack it as Doctor panel → Transcript → Patient panel, or (nicer) put the transcript on top and the two mic buttons side by side in a fixed bar at the bottom. Mic buttons must stay reachable without scrolling.

**Each speaker panel has:** name ("Doctor" / "Patient", with the patient label also written in their language if you can), language, a **big hold-to-speak button** (at least 96 px), and a status line.

**Status states for a panel** (make each one visually distinct):
| State | What the user sees |
|---|---|
| idle | "Hold to speak" |
| recording | button pulses / turns red, a timer "0:03", text "Listening… release to send" |
| sending | spinner, "Translating…", **both** mic buttons disabled |
| playing | "Speaking translation…" (a small speaker/wave animation) |
| error | short message + it goes back to idle |

**Transcript card (one per turn):**
- Speaker label + colour (doctor colour vs patient colour, so it's clear who said what).
- **Original text** (what they said) and **translation** (what the other person heard), clearly labelled, e.g. "Said (Urdu)" / "Heard (English)".
- Every text element uses `dir="auto"` so Urdu / Arabic / Persian show right-to-left automatically.
- Small meta line: detected language + delay, e.g. "Detected: Urdu · 3.4 s".
- **Language warning:** if `detected_language` ≠ the language we expected for that speaker, show a yellow note: "We heard Arabic, not Urdu. The translation may be wrong."
- A small "▶ replay" button to play the audio again.

**Urgent flags:** if `urgent_terms` is not empty, show a **red card** clearly aimed at the doctor, e.g. "⚠ Urgent: chest pain, shortness of breath". Use red **plus** an icon **plus** the word "Urgent" (never colour alone).

**Safety: "Is that what you said?"** (added Sat 14 Nov; the AI sometimes mis-hears, e.g. "released" became "burnt to death")
- Always show the **original text** to the person who spoke, in their own language, so they can see if it's wrong.
- **`unclear_words`:** underline / highlight these words inside the original text (amber, dotted underline), with a small note "Some words may be wrong. Please check".
- **`noisy: true`:** show an amber banner on that card: "Background noise: please check this was heard correctly."
- **`speech_clarity: "inaudible"`:** the translation is empty. Don't play audio; show "We couldn't hear that clearly. Please say it again." on the speaker's panel.
- Add a small **"That's not what I said ↺"** button on each card that just asks the speaker to record again (no backend call needed; the turn still counts).

**Bottom bar:** "Turns left: N" and an "End appointment" button (ask "Are you sure?" first).

### Screen 4: Summary
- Calls `POST /api/summary`, shows a loading state, then two boxes: **English summary** and **summary in the patient's language** (`dir="auto"`).
- "Copy" and "Download (.txt)" buttons for each.
- Then calls `POST /api/end` and shows a "Start new appointment" button (back to Screen 1).

### Footer (every screen)
> This project is a prototype and is not medical advice.

---

## 4. API contract (the backend gives you exactly this)

All endpoints live under `/api`, on the **same website** as the frontend, so just use relative URLs like `fetch("/api/turn")`. You don't need any CORS setup.
**Errors** always come back as `{"error": "<message>"}` with an HTTP status code. Show that message to the user.

### `POST /api/session`: start an appointment
Request (**JSON**):
```json
{ "access_code": "....", "doctor_lang": "en", "patient_lang": "ur" }
```
Response:
```json
{ "session_id": "abc123", "turns_left": 20 }
```
Wrong access code → **401**.

### `POST /api/turn`: one person speaks
Request (**multipart/form-data**, built with `FormData`):
| field | value |
|---|---|
| `session_id` | from `/api/session` |
| `speaker` | `"doctor"` or `"patient"` |
| `audio` | the recorded Blob, e.g. `formData.append("audio", blob, "turn.webm")` |

Response:
```json
{
  "original_text": "مجھے سینے میں درد ہے",
  "detected_language": "ur",
  "target_language": "en",
  "translation": "I have chest pain.",
  "urgent_terms": ["chest pain"],
  "unclear_words": [],
  "speech_clarity": "clear",
  "noisy": false,
  "audio_base64": "<mp3 as base64>",
  "timings": { "convert": 0.2, "translate": 2.1, "speak": 0.9, "total": 3.3 },
  "turns_left": 19
}
```
- `speaker` decides direction: patient → translated to English; doctor → translated to the patient's language.
- More than 20 turns → **429** with a friendly message. Show it, and disable the mic buttons.
- Far too much background noise → **400** with a friendly `error` ("There's too much background noise…"). Show it on the speaker's panel.
- `unclear_words`, `speech_clarity`, `noisy`: safety fields, see "Is that what you said?" above.
- `audio_base64` **may be empty** if both voice services fail. Then show the text only, with a small note "Audio not available right now. Please read the translation".
- Play the audio with: `new Audio("data:audio/mpeg;base64," + audio_base64).play()`

### `POST /api/summary`
Request (JSON): `{ "session_id": "abc123" }` → Response: `{ "summary_en": "...", "summary_patient_lang": "..." }`

### `POST /api/end`
Request (JSON): `{ "session_id": "abc123" }` → Response: `{ "ended": true }`

*(`POST /api/clone` exists only if we add voice cloning later. Ignore it for now.)*

---

## 5. Build order

### Step 1: Design tokens (CSS variables)
Put these at the top of `styles.css` and use them everywhere. Feel free to change the exact colours; that's your design call. Just keep the contrast high.
```css
:root {
  /* colours */
  --bg: #F4F8FA;            /* page background: very light blue-grey */
  --surface: #FFFFFF;       /* cards, panels */
  --text: #0F2530;          /* main text */
  --text-muted: #4A6572;
  --primary: #0B6E8C;       /* calm teal-blue: main buttons */
  --primary-hover: #095A73;
  --doctor: #1D4E89;        /* doctor accent (blue) */
  --patient: #0E7C66;       /* patient accent (teal-green) */
  --urgent: #C62828;        /* urgent flags, recording */
  --urgent-bg: #FDECEA;
  --warning: #8A5A00;       /* language mismatch text */
  --warning-bg: #FFF4D6;
  --border: #D5E1E7;
  --focus: #FFB81C;         /* keyboard focus ring: very visible */

  /* type */
  --font: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif;
  --text-sm: 0.875rem; --text-md: 1rem; --text-lg: 1.25rem; --text-xl: 1.75rem;

  /* spacing, shape */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px;
  --radius: 12px; --radius-lg: 20px;
  --shadow: 0 2px 8px rgba(15, 37, 48, 0.08);
  --tap: 48px;              /* minimum size for anything tappable */
}
```
**Fonts for the scripts:** Urdu, Arabic, Persian, Panjabi, Bengali and Gujarati need fonts that contain those letters. Simplest option: add **Noto Sans** families from Google Fonts (Noto Sans Arabic, Noto Nastaliq Urdu (optional), Noto Sans Gurmukhi, Noto Sans Bengali, Noto Sans Gujarati) to the font stack. Test that every language button renders properly, with no empty boxes. Credit Google Fonts / Noto (SIL Open Font License).

### Step 2: HTML structure
All 4 screens + footer in `index.html`, with semantic tags (`<main>`, `<section>`, `<button>`, `<label>`). No styling yet.

### Step 3: CSS + responsive layout
Desktop 3-column grid; below ~800 px stack it for phones. Big tap targets. Check it in Chrome DevTools' phone view.

### Step 4: JavaScript with a **mock backend**
At the top of `app.js`:
```js
const USE_MOCK = true;   // true = fake answers, false = real backend
```
Put all server calls in **one small `api` object** (`api.createSession`, `api.sendTurn`, `api.getSummary`, `api.endSession`). Each function checks `USE_MOCK`: if true it waits ~1.5 s (`await new Promise(r => setTimeout(r, 1500))`) and returns fake data in **exactly** the shapes from section 4; if false it calls `fetch`. The rest of the UI never knows which one it's talking to.

Make the mock realistic so you can test every state:
- access code `"wrong"` → throw a 401-style error
- count down `turns_left`; when it hits 0, return a 429-style error
- every 3rd turn include `urgent_terms: ["chest pain"]`
- sometimes return a different `detected_language` (tests the yellow warning)
- return `audio_base64: ""` (tests the "audio not available" path; no fake MP3 needed)
- sometimes return `unclear_words: ["درد"]` + `speech_clarity: "partly_unclear"`, sometimes `noisy: true`, and once `speech_clarity: "inaudible"` with `translation: ""` (tests the safety displays)
- include some Urdu/Arabic text so you can see RTL working

### Step 5: Microphone recording (hold-to-speak)
- Ask for the mic with `navigator.mediaDevices.getUserMedia({ audio: true })`.
- Record with `MediaRecorder`. **Pick a format the browser supports**: Chrome/Android/Firefox use `audio/webm`, while iPhone Safari uses `audio/mp4`. Check with `MediaRecorder.isTypeSupported(...)` and name the file to match (`turn.webm` or `turn.m4a`). The backend accepts both.
- Use **pointer events** so mouse and touch both work: `pointerdown` = start, `pointerup` / `pointercancel` / `pointerleave` = stop and send.
- Also support the **keyboard**: Space/Enter held down on the focused button = record.
- Stop phones from doing long-press stuff on the button: CSS `user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; touch-action: none;` and `preventDefault()` on `contextmenu`.
- Ignore very short presses (< 0.5 s): show "Hold the button while you speak". Auto-stop at 30 s.
- Only one person can record or send at a time. Disable both buttons while a turn is in progress.
- **The mic only works on `https://` or `http://localhost`.** Opening the file directly (`file://`) or from another device's IP address won't work. To test locally, run this inside the `frontend/` folder and open `http://localhost:8000`:
  ```
  python -m http.server 8000
  ```

### Step 6: Audio playback
- Autoplay the translation when it arrives.
- **iPhones block autoplay** after a network wait. Fix: on the very first tap of any mic button, create one `Audio` element and call `.play()` on it (silent). Then reuse that same element for every translation. If `play()` still fails, show a "▶ Tap to hear translation" button instead of failing silently.

### Step 7: Connect to the real backend
Set `USE_MOCK = false` and test with Malik's backend running (`http://localhost:8000`, where the backend serves your `frontend/` folder). Check that each response field ends up in the right place.

### Step 8: Polish
- Loading animations (spinner / pulsing dots) for "Translating…" and "Summarising…".
- Friendly error messages for:
  - **mic blocked:** "Please allow microphone access" + short how-to
  - **no mic found**
  - **network error / server down:** "Couldn't reach the server. Try again."
  - **limit reached (429):** show the server's message
  - **empty / too-short recording**
- Empty state for the transcript: "Hold a mic button and start speaking. The conversation will appear here."
- Transcript auto-scrolls to the newest card.
- Accessibility basics: every button has a clear label (`aria-label` on icon buttons), visible focus ring, `aria-live="polite"` on status text and the transcript so screen readers announce new turns, and colour contrast at least 4.5:1.

---

## 6. Done checklist

- [ ] All 4 screens work with `USE_MOCK = true`
- [ ] Looks good on a laptop **and** a phone (try a real phone once we deploy)
- [ ] Hold-to-speak works with mouse, touch and keyboard
- [ ] RTL languages (Urdu, Arabic, Persian) display right-to-left
- [ ] All 11 language names render (no empty boxes)
- [ ] Urgent flag card, language-mismatch warning, "audio not available" note all appear when expected
- [ ] Errors: wrong code, mic blocked, network down, 21st turn
- [ ] Works with `USE_MOCK = false` against the real backend
- [ ] Footer disclaimer on every screen
- [ ] Credits list written (fonts, icons, anything copied or adapted)

## 7. Useful for the write-up and demo

- Take **screenshots** of each screen (desktop + phone) as you go. We need them for the write-up and showcase page.
- Note anything users found **confusing** when they tried it. That goes in our usability results.
