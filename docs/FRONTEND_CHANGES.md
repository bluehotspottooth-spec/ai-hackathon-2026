# Frontend changes: what we changed from the AI-generated base

**Why this file exists:** our frontend started from an AI-generated design. To be honest and show our own work, we keep the original untouched and record every change we make on top of it, with the reason.

## The starting point (AI-generated, not ours)

| | |
|---|---|
| **Original file (never edited)** | [`docs/design/voicebridge_ORIGINAL.html`](design/voicebridge_ORIGINAL.html) |
| **Git tag** | `ai-original-mock` (on GitHub: Code → Tags). It shows exactly what the AI made, with a timestamp |
| **Made with** | Claude Code (AI coding assistant), 14 Nov 2026, based on our first Gemini Canvas mockup (`frontend/old_mockup/`) |
| **What it already did** | Multi-page site, appointment flow, chat-bubble transcript, tap-or-hold mic buttons, urgent banner, demo mode, API calls to our backend |

**Our working copy (FINAL):** [`frontend/voicebridge_FINAL.html`](../frontend/voicebridge_FINAL.html). All changes below happen there.

**How to compare old vs new at any time:** on GitHub, open `https://github.com/bluehotspottooth-spec/ai-hackathon-2026/compare/ai-original-mock...main` (the files were renamed on 15 Nov, so GitHub shows them as moved and changed). Or locally: `git diff ai-original-mock:docs/design/voicebridge_premium_mockup.html HEAD:frontend/voicebridge_FINAL.html` (at the tagged moment the original was still called `voicebridge_premium_mockup.html`).

---

## Our changes

One row per change. Take a **before and after screenshot** for the bigger ones (put them in `docs/design/screenshots/`). They're great for the write-up and the demo video.

"Who" says who decided and who built it. Where Claude Code wrote the code, it says so, to be honest about AI help.

| # | Date / time | Who | What we changed | Why (the user reason) | Commit |
|---|---|---|---|---|---|
| 1 | Sun 15 Nov | Team decision; files renamed by Claude Code | **Renamed** the AI original → `docs/design/voicebridge_ORIGINAL.html` (never edited) and our working copy → `frontend/voicebridge_FINAL.html`; the backend now serves the FINAL file at `/` | Makes it obvious what the AI made and what we made, for the team and for judges | `b133bfd` |
| 2 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **Logo:** two speech bubbles meeting (an outlined one and a solid one), on the teal brand colour. Used in the header, as the browser-tab icon, and as `frontend/logo.svg` for slides and the write-up. The wordmark is two-tone: "Voice**Bridge**" | The app is a bridge between two people's words; a clear mark makes it look like a real, trustworthy product rather than a demo | `42fafc4` |
| 3 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **Mic buttons:** bigger (60 → **88 px** on laptops, **72 px** on phones), **centred**, with the name and the "Tap or hold to speak" hint **underneath**. The same layout on laptop and phone (it used to be side-by-side on laptops and stacked on phones). Hover feedback added | It's the main thing people press. Bigger, centred targets are easier for older or anxious patients and on a phone lying on the desk, and the same layout everywhere means nobody has to relearn it | `42fafc4` |
| 4 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **Focus mode:** during an appointment the top menu and the "Start appointment" button are hidden, and the logo can't be clicked | Stops anyone accidentally leaving the conversation mid-appointment; less clutter while people are talking | `42fafc4` |
| 5 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **Quieter demo bar:** one small line under the buttons; on phones the "Demo mode" sentence is hidden (button area height 291 → 263 px) | The demo controls shouldn't compete with the real buttons, and phones need the space for the conversation | `42fafc4` |
| 6 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **Simpler empty screen:** one instruction ("Tap your button below, speak, then tap again…") instead of a 3-step list; the hint now leads with "Tap" | First-time users see one clear thing to do. Most people tap rather than hold | `42fafc4` |
| 7 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **Polish:** a subtle dot texture on the dark home banner, and soft shadows on the message bubbles | Looks more refined and professional without adding distractions | `42fafc4` |
| 8 | Sun 15 Nov | Chosen by the team, built with Claude Code | **New colour identity:** deep teal (trust) plus a warm **apricot accent**, warmer background tones, and a deeper teal gradient on the home banner. The main "Start an appointment" button is now apricot. Works in light and dark mode | The first version felt cold and generic. Warmth suits a health app for worried patients, and one bright accent makes the main action obvious | `cc1e58a` |
| 9 | Sun 15 Nov | Chosen by the team, built with Claude Code | **Animated home demo:** the example card now plays a live conversation in **Urdu → Polish → Arabic**: the doctor speaks (moving sound wave), the translation types itself out, the patient answers, and an urgent flag pops in. It starts as a complete still example, and is switched off for people who turn off animations on their device | Shows what VoiceBridge does in five seconds, without reading, and that it works across languages and scripts. A strong first impression for judges and users | `cc1e58a` |
| 10 | Sun 15 Nov | Chosen by the team, built with Claude Code | **Recording animation:** while someone speaks, a ring of 48 red sound bars pulses around the mic. In the real app it follows the microphone's actual sound level; in demo mode it imitates a voice. The recording text is shorter ("Listening… tap to send") | Clear, live proof that the app is hearing you, so people don't stop talking too early or wonder if the mic works | `cc1e58a` |
| 11 | Sun 15 Nov | Chosen by Ahmed, built with Claude Code | **Live caption spotlight:** the newest translation now appears **large at the top** of the appointment screen, like a live caption, saying who spoke, who it's for ("For the patient, in Urdu") and the time. Under it: what was originally said (unclear words underlined), the warning badges, and Replay / Not what I said. Older messages move into a smaller **"Earlier in this appointment"** list below, newest first. "Translating what the doctor said…" and "please say it again" now show in one line under the spotlight instead of piling up | In a real GP room the phone sits on the desk between two people. The patient needs to read the latest sentence **from across the desk**, in big text, without hunting through a chat. Bigger text also helps older patients and anyone with poor eyesight | `17a66ed` |
| 12 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **Use your own voice (optional):** a button on the empty appointment screen opens a pop-up: choose Doctor or Patient, **tick the consent box** (the record button stays off until you do), then talk for 10–45 s (a sample sentence is shown to read). Then "Own voice" appears under that person's mic button. Works in demo mode (pretend) and with the real backend (`/api/clone`) | Hearing the translation in the speaker's **own voice** makes it feel like a real conversation and makes it obvious who is talking. Consent first and "deleted when the appointment ends" are shown clearly, because a voice is personal data | `26bef70` |
| 13 | Sun 15 Nov | Requested by Ahmed, built with Claude Code | **"Your voice is not kept"** added to the warning box on the Home page: the voice copy is temporary and deleted when the appointment ends, and conversations and recordings aren't saved. The Safety page's "Nothing is kept" box says the same | People should know **before** they start that their voice won't be stored. It's personal data, and being upfront builds trust | `51e67df` |
| 14 | | Benet | *Your next changes go here (colours, spacing, wording…)* | | |
| 15 | | | *Connected to the backend (`USE_MOCK = false`) and tested with a real microphone* | | |

\* Rows 8–10 were made together in one commit.

**Checked after these changes:** laptop (1280 px) and phone (375 px) sizes, focus mode, recording state, demo conversation, no sideways scrolling on phones, and the page plus `logo.svg` served correctly by the backend. After #11: the full 6-turn demo puts the newest turn in the spotlight and the other 5 in the "Earlier" list (newest first), Urdu shows right-to-left, the urgent banner still appears, and starting a new appointment clears everything. Not checked yet: a real microphone and real phones (after deployment).

### Tips for writing the "why"
Judges care about **who it's for**. Good reasons sound like:
- "Bigger mic buttons, because patients may be elderly or anxious, and doctors use it on a phone on the desk"
- "Higher contrast, because some patients have poor eyesight"
- "Logo shows two speech bubbles meeting, because the app is a bridge between two languages"

Weak reasons: "looks nicer", "AI made it like this".

---

## Credit line for the write-up (edit as needed)
> The frontend was first drafted with AI design and coding assistants (Google Gemini Canvas, then Claude Code), then refined by our team: [list your main changes]. The original AI version is preserved in the repository (tag `ai-original-mock`) so the changes can be compared.
