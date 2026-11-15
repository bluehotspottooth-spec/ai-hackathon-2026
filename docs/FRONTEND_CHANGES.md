# Frontend changes: what we changed from the AI-generated base

**Why this file exists:** our frontend started from an AI-generated design. To be honest and show our own work, we keep the original untouched and record every change we make on top of it, with the reason.

## The starting point (AI-generated, not ours)

| | |
|---|---|
| **Original file (never edited)** | [`docs/design/voicebridge_premium_mockup.html`](design/voicebridge_premium_mockup.html) |
| **Git tag** | `ai-original-mock` (on GitHub: Code → Tags). It shows exactly what the AI made, with a timestamp |
| **Made with** | Claude Code (AI coding assistant), 14 Nov 2026, based on our first Gemini Canvas mockup (`frontend/old_mockup/`) |
| **What it already did** | Multi-page site, appointment flow, chat-bubble transcript, tap-or-hold mic buttons, urgent banner, demo mode, API calls to our backend |

**Our working copy:** [`frontend/index.html`](../frontend/index.html). All changes below happen there.

**How to compare old vs new at any time:** on GitHub, open `https://github.com/bluehotspottooth-spec/ai-hackathon-2026/compare/ai-original-mock...main` and look at `frontend/index.html`. Or locally: `git diff ai-original-mock -- frontend/index.html`.

---

## Our changes

One row per change. Take a **before and after screenshot** for the bigger ones (put them in `docs/design/screenshots/`). They're great for the write-up and the demo video.

| # | Date / time | Who | What we changed | Why (the user reason) | Commit |
|---|---|---|---|---|---|
| 1 | Sun 15 Nov, time | Benet | *Example: Made the mic buttons bigger (60 → 80 px) and moved the labels under them* | *Easier to hit for older patients and on phones* | *abc1234* |
| 2 | | | *Logo: designed the VoiceBridge logo* | | |
| 3 | | | *Refined colours / spacing* | | |
| 4 | | | *Connected to the backend (`USE_MOCK = false`)* | | |
| 5 | | | | | |

### Tips for writing the "why"
Judges care about **who it's for**. Good reasons sound like:
- "Bigger mic buttons, because patients may be elderly or anxious, and doctors use it on a phone on the desk"
- "Higher contrast, because some patients have poor eyesight"
- "Logo shows two speech bubbles meeting, because the app is a bridge between two languages"

Weak reasons: "looks nicer", "AI made it like this".

---

## Credit line for the write-up (edit as needed)
> The frontend was first drafted with AI design and coding assistants (Google Gemini Canvas, then Claude Code), then refined by our team: [list your main changes]. The original AI version is preserved in the repository (tag `ai-original-mock`) so the changes can be compared.
