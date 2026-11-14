# Errors, fixes and known issues

**The one place for every problem in VoiceBridge:** what went wrong, why, how we fixed it, and what's still open.
- **Part 1** (just below): a summary of all **known issues and limitations right now**. Read this first.
- **Part 2:** the full numbered log of every error, in the order we hit it.

Times are London time, Sat 14 Nov 2026 unless stated.

**Why we keep this:** it shows how we tested and debugged, and gives honest material for the "where it fails" part of the write-up.

| Symbol | Meaning |
|---|---|
| ✅ | Fixed |
| ⚠️ | Worked around / still open |
| 📊 | A real AI failure, kept as a result (not "fixed", because it's evidence) |

---

# Part 1: Known issues and limitations (current)

| # | Issue | How serious | What we've done / plan | Log |
|---|---|---|---|---|
| K1 | **Gemini sometimes mis-hears a word** and is fully confident about it (Urdu *rihaa* "released" → *jalaa* "burnt to death") | 🔴 High | Can't be fixed by prompting. Safety design: the speaker always sees what was heard in their own language, plus a "That's not what I said ↺" button (UI). Write-up: VoiceBridge supports, it doesn't replace, a professional interpreter | #14, #22 |
| K2 | **In heavy noise, Gemini invented whole sentences** (fake "chest pain") | 🔴 High | ✅ Fixed with 2 layers: a maths noise check blocks very noisy audio before the AI; the prompt says "never invent, say [inaudible]". Tested 4/4 | #23 |
| K3 | **The AI's own "I'm unsure" signal is unreliable**: it said "clear" even when wrong | 🟠 Medium | We rely on the *objective* noise check for warnings; `unclear_words` is kept but never trusted alone | #22 |
| K4 | **Medical layer not yet proven better than the baseline**; on 1 general sentence it was worse | 🟠 Medium | Expected (it's built for GP talk). Must be proven in the medical test C3 | #15 |
| K5 | **Random slow answers from Google** (11 s, 22 s, 54 s instead of 3–4 s) | 🟠 Medium | 20-second limit + 1 retry on translation (tested). Report real latency in C4 | #27 |
| K6 | **Backup voice can hang** and its time limit isn't enforced | 🟡 Low (only matters if ElevenLabs also fails) | Open: options in #28 | #28 |
| K7 | **ElevenLabs credits limited**: ~400 spoken turns left this month (free plan) | 🟡 Low | Backup voice (Gemini) takes over automatically if credits run out. Testers: test translation without speech | #19, #26 |
| K8 | **Medical audio goes to Google and ElevenLabs servers**; free plans may use data to improve products | 🟠 Medium (for real use) | Prototype uses only test data (FLEURS, AI voices, team voices). Write-up: not for real patients without an NHS-approved data agreement | — |
| K9 | **Panjabi script**: we write Gurmukhi, but many UK Panjabi speakers (Pakistani heritage) read Shahmukhi | 🟡 Low | Ask a Panjabi speaker | #16 |
| K10 | **Only checked by AI so far**: no native speaker has listened to the voices or read the translations yet | 🟠 Medium | Native-speaker checks in C3/C4 (hackathon rule) | #19 |
| K11 | **FLEURS English reference translations not downloaded** (Hugging Face server error) | 🟡 Low | Retry later; needed for C2 | #13, #29 |
| K12 | **2 FLEURS Urdu clips (1806, 1930) were used for building**, so they can't count as test results | Rule | Excluded from C2 (see note at the bottom) | — |
| K13 | **Gemini free-tier limits**: many fast requests may get slowed down | 🟡 Low | Spread tests out; retry is built in | #25 |
| K14 | **Pre-hackathon commits** (Fri 13 Nov, repo test only) | 🟡 Low | Explain honestly if asked | #8 |
| K15 | **Frontend choice (HTML vs Gradio) not decided** | 🟠 Medium (timeline) | Team decision needed today | — |
| K16 | **Real phones/mics not tested yet**: noise thresholds were set on artificial noise | 🟠 Medium | Test on real devices after deploy; adjust `NOISE_BLOCK_DB` / `NOISE_WARN_DB` | #23 |

---

# Part 2: Full error log

## Setup (step A1)

### 1. ✅ Git saved the wrong name
- **What happened:** `git config --global user.name ahmed khan` (no quotes) ran without an error, but Git saved only `ahmed`. An earlier paste had also saved the placeholder `Your Name`, so Git had **two** names.
- **Cause:** PowerShell splits words on spaces, so without quotes Git received `ahmed` as the name and `khan` as a separate (ignored) argument.
- **Fix:** `git config --global --replace-all user.name "Ahmed Khan"`. The quotes keep it as one value, and `--replace-all` removes both wrong entries.
- **Lesson:** put text with spaces in quotes in the terminal.

### 2. ✅ Couldn't make the first commit
- **What happened:** Git refused to commit.
- **Cause:** no email set in Git yet. Git needs a name **and** email to label every commit.
- **Fix:** `git config --global user.email "..."`.

### 3. ✅ Couldn't find the `.env` file
- **What happened:** `.env` wasn't visible in the `hackathon` folder.
- **Cause:** it's one level deeper, in `hackathon\voicebridge\.env`.
- **Fix:** opened the `voicebridge` folder in VS Code (File → Open Folder).

### 4. ✅ ElevenLabs key "missing permissions" (HTTP 401)
- **What happened:** text-to-speech worked, but listing voices and checking credits failed: *"The API key you used is missing the permission voices_read / user_read"*.
- **Cause:** the key was created as a *restricted* key (good for security), but two permissions weren't switched on.
- **Fix:** edited the key on ElevenLabs: Voices = Read, User = Access. The key value didn't change, so `.env` stayed the same.
- **Lesson:** a restricted key is safer, so give it only what the app needs, then **test each permission**.

## Audio conversion (step A2)

### 5. ✅ Test script couldn't find a file (Windows path style)
- **What happened:** `FileNotFoundError: '/c/Users/...'`.
- **Cause:** we mixed path styles. Git Bash writes `/c/Users/...`, but Python on Windows needs `C:\Users\...`.
- **Fix:** used the Windows-style path in Python.

## GitHub (team repo)

### 6. ✅ Our project and the team repo had separate histories
- **What happened:** the team repo already had files (README, briefs, mockup), and our local project had its own commits. Git saw them as two unrelated projects.
- **Fix:** `git merge origin/main --allow-unrelated-histories` joined the two histories into one.

### 7. ✅ Merge conflict in `UI_BRIEF_GRADIO.md`
- **What happened:** the same file existed in both places with one line different, so Git couldn't choose.
- **Fix:** kept our newer version (it had the Gradio 6.32 note), then finished the merge.
- **Lesson:** this is why we gave everyone **their own folder**: two people editing the same file causes conflicts.

### 8. ⚠️ Commits from before the hackathon
- **What happened:** the repo has 3 commits from **Fri 13 Nov 22:14–22:17** (repo creation + a "hello world" test file), before the 5:00 AM Saturday start.
- **What we did:** nothing to fix. The test files were deleted Saturday 09:43 and none of it is project code. Noted here so we can explain it honestly if asked.

## Gemini translation (step A3)

### 9. ✅ Google's docs and API had changed
- **What happened:** the old docs address (`ai.google.dev`) now redirects to `aistudio.google.com/docs`, and the recommended way to call Gemini is now the **Interactions API** (`client.interactions.create`), not the older `generate_content` style found in most online tutorials.
- **Fix:** read the current official docs (as our brief requires) and checked the installed SDK (google-genai 3.3.0) supports `interactions`.
- **Lesson:** tutorials go out of date fast, so check the official docs.

### 10. ✅ Newest model far too slow for a live conversation
- **What happened:** `gemini-4-hydrogen` (recommended by Google for new projects) took **56 s, 104 s and 135 s** per turn.
- **Fix:** benchmarked 4 models on the same 13-second clip:

  | Model | Time | Urgent symptoms flagged? |
  |---|---|---|
  | gemini-3.5-flash-lite | **4.0 s** | ✅ both |
  | gemini-3.1-flash-lite | 4.7 s | ✅ both |
  | gemini-4-hydrogen | 56–135 s | ✅ both |
  | gemini-3.6-flash | failed (see #12) | — |

  We switched the default to **gemini-3.5-flash-lite**: 30× faster with the same urgent flags.

### 11. ✅ Urdu text crashed the test printout (`'charmap' codec can't encode`)
- **What happened:** the Gemini calls worked, but printing Urdu to the Windows terminal crashed.
- **Cause:** the Windows terminal defaults to an old, non-Unicode text encoding. Our fix (`PYTHONIOENCODING`) was ignored because we ran Python in isolated mode (`-I`).
- **Fix:** run Python with `-X utf8` (forces Unicode).

### 12. ⚠️ `gemini-3.6-flash` request failed
- **What happened:** our request failed for this model only.
- **Status:** not investigated (we didn't need it, since Flash-Lite was faster). Possibly it needs different settings.

### 13. ⚠️ Hugging Face dataset service down (HTTP 500)
- **What happened:** downloading the 2 Urdu FLEURS clips worked, but looking up their **English reference translations** failed 3 times: *"Authentication check on the Hugging Face Hub failed or timed out... temporary internal issue."*
- **What we did:** stopped retrying (our rule: stop after 2 failures). Ran Milestone 1 without the English references.
- **To do:** fetch the English references later (FLEURS `en_us` same IDs, or FLORES+).

### 14. 📊 Milestone 1: Gemini mis-heard an Urdu sentence (both modes)
FLEURS Urdu clip **1930** (6 s). The correct Urdu means: *"Six hostages, including children and elderly people, were released early, along with the Filipino photographers."*

| | What Gemini heard | Translation |
|---|---|---|
| **VoiceBridge** | Wrote the transcript in **Hindi (Devanagari) script**, not Urdu script. Heard "Filipino" as "kal pani" (yesterday… water) and "kidnapped" (*aghwa*) as "Afghan" | *"Six **Afghan martyrs**… were released"* ❌ |
| **Baseline** | Wrote it in Roman letters. Heard "released" (*rihaa*) as "burnt" (*jalaa*) | *"…six kidnapped people… were **burnt to death**"* ❌❌ |

- **Why it matters:** the baseline turned "released" into "burnt to death", the opposite meaning. In a GP appointment, a mistake like that could be dangerous.
- **Likely causes:** spoken Urdu and Hindi sound almost identical, so the model drifted into Hindi script; a short 6 s clip with names gives little context; similar-sounding words (*rihaa* / *jalaa*).
- **Fix to try:** tell the model the exact **script** for each language (Urdu = Perso-Arabic script, etc.). See the important note below.
- **Update (after the fix, see #16):** the script problem is ✅ fixed: Urdu script in 3/3 runs. The **hearing** mistake is 📊 still there: *"were burnt to death"* in 3/3 runs. A prompt can't fix a sound being mis-heard, so this stays as a known failure.

### 15. 📊 Milestone 1: medical layer made one general sentence *worse*
FLEURS Urdu clip **1806** (12 s): both modes transcribed it almost perfectly.
- **Baseline:** *"mild **pollution** was not as much of an issue…"* ✅ (correct)
- **VoiceBridge:** *"mild **flooding** was not as much of an issue…"* ❌
- **Cause:** VoiceBridge's transcript misspelt تلوث (pollution) as تلویس, so the translation guessed "flooding".
- **Takeaway:** our medical layer is designed for **GP conversations**, not general news sentences like FLEURS. We must measure it on **medical** sentences (test C3) before claiming it helps.
- **Update (after the fix, see #16):** ✅ now says "pollution" in 3/3 runs. Writing the transcript in proper Urdu script fixed the misspelling that caused "flooding".

### 16. ✅ Fix: exact script rules per language
- **What we changed:** `prompts.py` now has a `SCRIPTS` table (e.g. Urdu = *"Urdu script (Perso-Arabic). Never Hindi/Devanagari, never Roman letters"*, Panjabi = Gurmukhi, Persian = Persian script) and tells Gemini which script to use for the transcript **and** the translation. It also explains that spoken Urdu and Hindi sound alike.
- **Re-test** (both dev clips, 3 runs each, so we're not fooled by one lucky answer):

  | | Before fix | After fix |
  |---|---|---|
  | Transcript script | Hindi or Roman letters | **Urdu script, 6/6** ✅ |
  | Clip 1806 "pollution" | "flooding" ❌ | **"pollution", 3/3** ✅ |
  | Clip 1930 "released" | "Afghan martyrs" ❌ | "burnt to death", 3/3 ❌ (mis-heard sound, see #14) |
  | Speed | 3–4 s | 2.5–3.7 s |

- **Caution:** we tested the fix on the same 2 clips we used to find the problem, so this proves the fix works on *these* clips only. The real measure is the FLEURS evaluation (C2) on **other** clips.
- **Open question for a native speaker:** Panjabi in the UK is written in **Gurmukhi** (mostly Indian-heritage speakers) *or* **Shahmukhi** (Perso-Arabic; mostly Pakistani-heritage speakers). We chose Gurmukhi for now (it matches FLEURS). Worth asking a Panjabi speaker.

## Speech / text-to-speech (step A4)

### 17. ✅ ElevenLabs key missing the "Models" permission
- **What happened:** asking ElevenLabs which model supports which language failed: *"missing the permission models_read"*.
- **Fix:** instead of changing the key again, we read the same information in ElevenLabs' official model docs. (The app doesn't need this permission to work.)

### 18. ✅ Older ElevenLabs models don't speak 5 of our languages
- **What we found:** `eleven_multilingual_v2` and `eleven_flash_v2_5` (used in most tutorials) **don't support Urdu, Panjabi, Bengali, Gujarati or Persian**, so almost half our users would have had no audio.
- **Fix:** chose `eleven_v4_turbo`. The docs list all 11 languages, and our test confirmed it (#19).

### 19. 📊 Round-trip test of speech in all 11 languages
- **How:** Gemini translated one GP sentence (*"Are you allergic to any medicines? Please tell me if you are pregnant."*) into all 11 languages, ElevenLabs spoke each one, and then our Gemini pipeline **listened back**. If the pronunciation were poor, the transcript would come back different.
- **Result:** all 11 recognised as the right language; **95–100% text match**; speech generated in 0.6–1.1 s. Details: `tests/results/milestone2/tts_all_languages.json`.
- **Limit of this test:** it uses AI to check AI. A native speaker still has to listen and judge whether it sounds natural (part of C4).

### 20. ✅ Polish: the voice read a slash out loud ("pani ukośnik pan")
- **What happened:** the Polish translation wrote *"pani/pan"* (Mrs/Mr) to cover both genders, and ElevenLabs read the "/" as the word *ukośnik* ("slash").
- **Cause:** written-style shortcuts don't work when text is spoken aloud.
- **Fix (two layers):**
  1. **Prompt rule 10:** never use slashes or brackets for alternatives; choose ONE natural form, using conversation clues for the listener's gender.
  2. **Safety net in `voice.py`:** any "/" is replaced with a comma (a short pause) before speaking.
- **Re-test (3 runs):** *"Czy ma pani uczulenie na jakieś leki?…"*, one form, no slash, 3/3 ✅.

### 21. ✅ Arabic text used a Persian letter (أدویه instead of أدوية)
- **What happened:** in the all-languages test, the Arabic translation used the Persian form of a letter (Arabic and Persian share an alphabet but differ in a few letters).
- **Fix:** prompt rule 11: use only the target language's own alphabet. **Re-test:** correct Arabic أدوية in 3/3 runs ✅.
- **Our own mistake while checking:** our first automatic check wrongly flagged the correct Arabic, because we included ه, which is a normal Arabic letter too. We fixed the check to look only for the Persian-only letters ی and ک. Lesson: test your tests.

## Safety features (afternoon)

### 22. 📊 The AI doesn't admit when it mis-hears ("unclear words")
- **What we built:** a new field `unclear_words`, where Gemini lists the words it isn't sure it heard correctly, so the screen can highlight them.
- **Test:** clip 1930 (where it mis-hears "released" as "burnt"), 3 runs: **0/3 flagged anything**. It was confidently wrong every time. It also said "clear" on a lightly noisy clip where it got a word wrong.
- **Lesson:** AI models are often *confidently wrong*; asking them to report doubt isn't reliable. We kept the field (it costs nothing), but our real safety comes from objective checks (#23) and from showing the speaker what was heard (K1).

### 23. ✅ In heavy noise, the AI **invented** medical sentences (most serious bug so far)
- **What happened:** we added heavy background noise to clip 1806 (about pollution). VoiceBridge returned *"Doctor, I have very sharp **chest pain** and I am having difficulty breathing"*, a sentence **never said**, with an urgent flag, in 2/2 runs. The baseline invented *"my throat is very bad and I have a cough"* in 1 of 2 runs.
- **Cause:** when the model can't hear, it guesses, and our "GP appointment" instructions pushed the guess towards medical symptoms (*priming*).
- **Fix, layer 1: an objective noise check in `audio.py`** (plain maths, no AI). We measure the "contrast" between the loud parts (speech) and the quiet gaps between words (background):

  | Clip | Contrast | What Gemini did | Our rule |
  |---|---|---|---|
  | Clean speech (FLEURS, AI voices, robot) | 23–28 dB | correct | ✅ pass |
  | Light noise | 5.7 dB | mostly right, one word wrong | ⚠️ pass **with a warning** (< 12 dB) |
  | Medium / heavy noise | 2.9 dB | nonsense / invented symptoms | 🛑 **blocked** (< 4 dB): "too much background noise, please try again" |

- **Fix, layer 2: stricter prompt.** New rule 0, *"NEVER INVENT… being in a GP appointment does NOT mean the audio is about health… say [inaudible]"*; a required `speech_clarity` answer (clear / partly_unclear / inaudible); and an extra warning in the request when layer 1 measured noise.
- **Re-test of layer 2 on its own** (heavy and medium noise sent straight to Gemini, bypassing layer 1): **"inaudible", no translation, no urgent flags: 4/4** (before: invented chest pain 2/2).
- **Regression check:** clean clips still translate normally, and urgent flags still work (chest pain + breathlessness on the English test).
- **Limit:** thresholds were set on *artificial* pink noise; real rooms and phone mics may differ (K16).

### 24. ✅ Our old audio test clips were beeps, and now count as "noise"
- **What happened:** the A2 format test used pure tones. The new noise check rejects them, because a steady beep has no gaps between words.
- **Fix:** redid the format test with real speech converted to webm, m4a, wav and ogg: **all 4 pass**. (The beep test wasn't a fair test of speech anyway.)

### 25. ✅ Automatic retry for temporary Gemini failures
- **Why:** busy servers, rate limits or network blips shouldn't ruin a turn.
- **What:** `pipeline.py` now tries **twice** (1.5 s pause) before showing "please try again".
- **Test:** asked for a model that doesn't exist → *attempt 1 failed, attempt 2 failed* → user sees the friendly message, no crash ✅.

### 26. ✅ Backup voice: "model not found" until we used the beta API
- **What we built:** if ElevenLabs fails (credits used up, service down), `voice.py` automatically switches to **Gemini's own voice** (`gemini-3.8-flash-lite-tts`), with two different voices again (Charon / Sulafat).
- **Error:** every request failed with *"Model 'gemini-3.8-flash-lite-tts' not found"*, even though Google's docs list it.
- **Cause:** voice models only work through the **beta version** of the API (`v1beta`); Google's example uses it, our client didn't.
- **Fix:** one line, `http_options={"api_version": "v1beta"}`.
- **Test (listen-back, all 11 languages):** right language **11/11**, **93–100%** word match, **including Urdu** (which Google's list didn't mention). 3.3–4.7 s each (slower than ElevenLabs' ~1 s). **Automatic switch test:** ElevenLabs given a bad voice → Gemini voice took over ✅. Results: `tests/results/milestone2/backup_voice_all_languages.json`.

### 27. ⚠️ Random slow answers from Google
- **What happened:** usually 3–4 s, but we saw 11 s, 22 s and once **54 s** (Bengali, backup voice).
- **Fix (translation):** 20-second time limit per attempt, then retry. **Tested** that the limit is really enforced (set to 0.01 s → gave up after 2 attempts in 2 s) ✅.

### 28. ⚠️ OPEN: the backup voice can hang, and its time limit isn't enforced
- **What happened:** after #27, a backup-voice request didn't answer for **over 90 seconds** (twice), even with `timeout=20`. Earlier the same requests took 3–5 s, so Google's voice service seems to have slowed down or stalled, and the SDK doesn't apply our time limit to it.
- **Impact:** only when ElevenLabs *also* fails. Then a turn could hang instead of showing text only.
- **Options:**
  1. **Hard stop of our own**: run the backup voice in a separate thread and stop waiting after 15 s, then show text only. *(Recommended: simple, doesn't depend on Google's SDK.)*
  2. Remove the backup voice and accept "text only" if ElevenLabs fails.
  3. Use a different backup (e.g. the browser's built-in voice, in the frontend). No server needed, but quality varies by phone, and some languages may be missing.

### 29. ⚠️ Hugging Face still down (update to #13)
- Retried fetching the FLEURS English references: still *HTTP 500*. Try again later.

---

## ⚠️ Important note for testing (C2)
FLEURS Urdu clips **1806 and 1930** were used while **building** the system (Milestone 1, and any prompt fixes from #14). Under the hackathon rules, results must come from test data **not used to build the system**, so **these two clips must be left out of the FLEURS evaluation**.
