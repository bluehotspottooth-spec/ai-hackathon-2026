# VoiceBridge: UI brief (Gradio version)

This replaces the earlier HTML/CSS/JS brief (`UI_BRIEF.md`). The frontend is now built with **Gradio**, in Python. Give this whole file to your AI assistant first and tell it to follow the "Rules" section.

> **Deadline:** feature freeze **Sunday 1 PM** (London). We submit Sunday evening.
> **Your files:** `frontend/app.py` (the Gradio UI) and `frontend/mock_service.py` (fake backend for testing). Don't edit anything in `backend/`; that's Malik's.

---

## 1. What we're building (30-second version)

**VoiceBridge** is a live voice translator for **GP appointments in the UK**.

- **User:** a patient with limited English who needs to explain their symptoms to a GP and understand what the GP says back.
- A doctor and a patient share **one screen** (laptop or phone).
- One person records what they say. A few seconds later the other person **hears the translation spoken aloud**, and a **two-language transcript** appears on screen.
- Urgent symptoms (e.g. "chest pain", "can't breathe") show up as a **red flag for the doctor**.

The UI should feel **calm, trustworthy and medical**, not like a default demo.

---

## 2. Rules (for you and your AI assistant)

1. **Python + Gradio only.** Use `gr.Blocks` (not `gr.Interface`) so we control the layout.
2. **Check the current Gradio docs** (https://www.gradio.app/docs) for argument names. Gradio changes between versions. Write down which version you installed (`pip show gradio`).
3. Work in **small steps**: build one thing, run it, check it, then move on.
4. Make sure you can **explain every part** yourself, because judges will ask questions live.
5. **No API keys in your code.** You never call Gemini or ElevenLabs yourself. You only call the 4 service functions in section 4.
6. **Don't change the service functions' names, inputs or outputs** (section 4) without agreeing it with Malik first.
7. All code must be written **during the hackathon**. Commit to the shared repo often, touching only `frontend/`.
8. **Credit everything** you use (Gradio, themes, fonts, icons) with link + licence.
9. Simple, readable code with short comments.

---

## 3. How your part connects to the backend

```
frontend/app.py  (Gradio UI: your part)
      │  calls 4 plain Python functions
      ▼
backend/service.py  (Malik)          frontend/mock_service.py  (you, for testing)
  create_session()                     same 4 functions, fake answers
  run_turn()
  get_summary()
  end_session()
      │
      ▼
Gemini (translate) + ElevenLabs (speak) + glossary + sessions
```

At the top of `app.py`:
```python
USE_MOCK = True   # True = fake answers, False = real backend

if USE_MOCK:
    from frontend import mock_service as service
else:
    from backend import service
```
The rest of your code only ever calls `service.create_session(...)`, `service.run_turn(...)` and so on. **Joining up later means changing `True` to `False`.** That's why the function shapes in section 4 must match exactly.

At the end, Malik's `backend/main.py` will host your Gradio app on the same website as the API (using `gr.mount_gradio_app`). You just need to expose your app as a variable called **`demo`** (`demo = gr.Blocks(...)`) and **not** call `demo.launch()` at import time. Put that inside `if __name__ == "__main__":` so you can still run it on its own while building.

---

## 4. The service functions (your "contract" with the backend)

They return plain Python dicts with the **same fields as the backend's `/api` endpoints**.

```python
class ServiceError(Exception):
    """Raised for user-facing problems. .message is safe to show on screen."""
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status   # 401 wrong code, 429 too many turns, 400 bad audio, 500 other
```

### `create_session(access_code: str, doctor_lang: str, patient_lang: str) -> dict`
Returns `{"session_id": "abc123", "turns_left": 20}`.
Wrong access code → raises `ServiceError(..., 401)`.

### `run_turn(session_id: str, speaker: str, audio_path: str) -> dict`
- `speaker` is `"doctor"` or `"patient"`. The patient is translated to English; the doctor is translated to the patient's language.
- `audio_path` is the path of the recorded file (Gradio gives you this).

Returns:
```python
{
  "original_text": "مجھے سینے میں درد ہے",
  "detected_language": "ur",
  "target_language": "en",
  "translation": "I have chest pain.",
  "urgent_terms": ["chest pain"],
  "audio_base64": "<mp3 as base64, or '' if not available>",
  "timings": {"convert": 0.2, "translate": 2.1, "speak": 0.9, "total": 3.3},
  "turns_left": 19,
}
```
More than 20 turns → `ServiceError(..., 429)`. Empty or too-short audio → `ServiceError(..., 400)`.

### `get_summary(session_id: str) -> dict`
Returns `{"summary_en": "...", "summary_patient_lang": "..."}`.

### `end_session(session_id: str) -> dict`
Returns `{"ended": True}`.

**Malik:** put `ServiceError` in `backend/service.py`. The mock should import it from there, or keep an identical copy until the backend file exists.

---

## 5. Screens

Build all 4 screens inside one `gr.Blocks`, each as a `gr.Column(visible=...)`. Switch screens by returning `gr.update(visible=True/False)` (or `gr.Column(visible=...)` in newer Gradio) from your event handlers.

Keep per-user data in **`gr.State`**: `session_id`, `patient_lang`, and the chat history. Never use global variables, because two people using the app at once would see each other's data.

### Screen 1: Access
- Title + tagline ("Speak to your GP in your own language").
- `gr.Textbox(type="password", label="Access code")` + "Next" button.
- Just store the code in `gr.State` here, then go to Screen 2.

### Screen 2: Setup
- "Which language does the patient speak?" Use `gr.Radio` or `gr.Dropdown` with labels in the native language first:

| Code | Label | Right-to-left? |
|---|---|---|
| `pl` | Polski · Polish | |
| `ro` | Română · Romanian | |
| `pa` | ਪੰਜਾਬੀ · Panjabi | |
| `ur` | اردو · Urdu | **yes** |
| `pt` | Português · Portuguese | |
| `es` | Español · Spanish | |
| `ar` | العربية · Arabic | **yes** |
| `bn` | বাংলা · Bengali | |
| `gu` | ગુજરાતી · Gujarati | |
| `it` | Italiano · Italian | |
| `fa` | فارسی · Persian | **yes** |

  Tip: choices can be `(label, value)` pairs, so the user sees "اردو · Urdu" and your code gets `"ur"`.
- Doctor is always English (`"en"`). Show this as text.
- "Begin appointment" → `service.create_session(code, "en", lang)`. On `ServiceError` with status 401, show the message and send them back to Screen 1.

### Screen 3: Appointment (main screen)

Layout with `gr.Row` + `gr.Column`:
```
┌───────────────┬───────────────────────────┬───────────────┐
│ DOCTOR        │  TRANSCRIPT (gr.Chatbot)  │ PATIENT       │
│ English       │                           │ اردو Urdu     │
│ [🎤 record]   │  doctor bubbles one side, │ [🎤 record]   │
│               │  patient bubbles the other│               │
└───────────────┴───────────────────────────┴───────────────┘
 [⚠ URGENT box]   [🔊 translation player]   Turns left: 17   [End appointment]
```
On phones, Gradio stacks columns automatically. Check that the order still makes sense (`min_width` on columns helps).

**Mic inputs:** one per speaker:
```python
doctor_mic = gr.Audio(sources=["microphone"], type="filepath", label="Doctor: record")
```
Use the mic's **`.stop_recording(...)`** event to send the turn automatically when they press stop, so nobody needs a separate "Send" button. After the turn, clear the mic (return `None`) so it's ready for the next recording.

**What one turn does** (one handler function, e.g. `handle_turn(speaker, audio_path, state...)`):
1. If `audio_path` is empty → `gr.Warning("Nothing was recorded. Try again.")` and stop.
2. Call `service.run_turn(session_id, speaker, audio_path)` inside `try/except ServiceError`.
3. Add a message to the Chatbot:
   - Doctor as one role and patient as the other, so they appear on opposite sides.
   - Text like: `**Said (Urdu):** …` then `**Heard (English):** …`, then a small line `Detected: Urdu · 3.3 s`.
   - **RTL:** wrap the Urdu/Arabic/Persian text in `<div dir="auto">…</div>` (or use the Chatbot's `rtl` option). **Test that it actually displays right-to-left.**
4. **Language warning:** if `detected_language` isn't what we expected for that speaker, add "⚠ We heard Arabic, not Urdu. The translation may be wrong."
5. **Urgent flag:** if `urgent_terms` is not empty, show a red `gr.HTML` / `gr.Markdown` box for the doctor: "⚠ URGENT: chest pain". Use red + icon + the word "URGENT" (never colour alone).
6. **Play the translation:** decode `audio_base64` to a temporary `.mp3` file and return its path to an output `gr.Audio(autoplay=True)`. If `audio_base64` is empty, show "Audio not available for this language" instead.
7. Update "Turns left: N". At 429, show the message and make both mics non-interactive.

Gradio shows its own loading spinner while the handler runs. Add `gr.Info("Translating…")` or a status line if you want something clearer.

**End appointment** button → go to Screen 4.

### Screen 4: Summary
- Call `service.get_summary(session_id)`, show `summary_en` and `summary_patient_lang` in two `gr.Textbox(lines=8)` boxes. Textboxes have a copy button built in (check the docs for `show_copy_button`).
- Optional: `gr.DownloadButton` / `gr.File` for a `.txt` download.
- Then call `service.end_session(session_id)`. Add a "New appointment" button that resets the state and goes back to Screen 1.

### Footer (every screen)
`gr.Markdown("This project is a prototype and is not medical advice.")` outside the screen columns, so it's always visible.

---

## 6. Build order

1. **Setup:** `pip install gradio` inside the project's virtual environment (`.venv`) (Malik will add it to `requirements.txt`). Run a "hello world" `gr.Blocks` to check it works.
2. **`mock_service.py`:** the 4 functions with fake answers in **exactly** the section 4 shapes. Add `time.sleep(1.5)` so it feels real. Make it test every case:
   - access code `"wrong"` → `ServiceError("That code didn't work.", 401)`
   - count down `turns_left`; at 0 → `ServiceError("This appointment has reached its 20-turn limit.", 429)`
   - every 3rd turn → `urgent_terms: ["chest pain"]`
   - sometimes a different `detected_language` (tests the warning)
   - `audio_base64: ""` (tests the "no audio" path)
   - Urdu/Arabic example text (tests RTL)
3. **Layout:** all 4 screens with the right components, no logic yet.
4. **Screen switching + state:** access → setup → appointment → summary → back to start.
5. **The turn handler:** mic → mock → chatbot bubble, urgent box, warning, turns left.
6. **Styling:** use a calm theme, e.g. `gr.themes.Soft(primary_hue="teal", secondary_hue="blue")`, plus a little custom CSS (`css=` argument) for the urgent box and bigger mic areas. Choose a font that supports all the scripts (Gradio themes accept Google Fonts, e.g. "Noto Sans"). Make sure all 11 language names render, with no empty boxes.
7. **Join up:** set `USE_MOCK = False` with Malik once his `service.py` works.
8. **Phone test** on the Hugging Face link (the mic needs `https://`, which HF provides).

Run while building: `python -m frontend.app` from the project root (or `gradio frontend/app.py` for auto-reload; check the docs).

---

## 7. Known Gradio limits (be honest about these in the write-up)

- The mic is **click to record, click to stop**, not hold-to-speak.
- **Autoplay may be blocked on iPhones.** Keep the audio player visible so people can press ▶.
- Layout and styling are less flexible than a hand-made web page. Focus on clarity, not fancy design.

---

## 8. Done checklist

- [ ] All 4 screens work with `USE_MOCK = True`
- [ ] Per-user data is in `gr.State`, not globals
- [ ] App is exposed as `demo`, and `launch()` only runs under `if __name__ == "__main__":`
- [ ] Doctor and patient turns appear on opposite sides of the transcript
- [ ] RTL works for Urdu, Arabic and Persian
- [ ] Urgent box, language warning and "no audio" note appear when expected
- [ ] Errors handled: wrong code, empty recording, 21st turn
- [ ] Works with `USE_MOCK = False` against Malik's backend
- [ ] Works on a phone via the Hugging Face link
- [ ] Footer disclaimer visible
- [ ] Credits list written
- [ ] Screenshots of each screen (laptop + phone) saved for the write-up
