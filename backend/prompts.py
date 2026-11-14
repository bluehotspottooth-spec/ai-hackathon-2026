"""
prompts.py: the instructions we give Gemini.

There are TWO versions, so we can measure what our medical layer adds:

1. BASELINE: a plain "transcribe, detect the language, translate" request.
   This is what anyone would get by using Gemini directly.

2. VOICEBRIDGE (medical layer): our GP-specific rules + urgent-symptom
   flagging + glossary terms. This is OUR work on top of the AI, and the
   tests compare it against the baseline.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Use AI-drafted (not yet checked) glossary translations as suggestions? (see _glossary_block)
USE_UNVERIFIED_GLOSSARY = os.getenv("USE_UNVERIFIED_GLOSSARY", "true").lower() == "true"

# Our 11 patient languages + English. Code -> English name.
# Codes are ISO 639-1 (the standard 2-letter language codes).
LANGUAGES = {
    "en": "English",
    "pl": "Polish",
    "ro": "Romanian",
    "pa": "Panjabi",
    "ur": "Urdu",
    "pt": "Portuguese",
    "es": "Spanish",
    "ar": "Arabic",
    "bn": "Bengali",
    "gu": "Gujarati",
    "it": "Italian",
    "fa": "Persian",
}

# The writing system to use for each language.
# Why: in Milestone 1, Gemini wrote Urdu speech in Hindi (Devanagari) script,
# because spoken Urdu and Hindi sound almost the same. Naming the script
# explicitly tells the model exactly what we expect.
SCRIPTS = {
    "en": "Latin alphabet",
    "pl": "Latin alphabet with Polish letters (ą, ę, ł, ż...)",
    "ro": "Latin alphabet with Romanian letters (ă, â, î, ș, ț)",
    "pa": "Gurmukhi script (ਪੰਜਾਬੀ)",
    "ur": "Urdu script (Perso-Arabic, as in اردو). Never Hindi/Devanagari, never Roman letters",
    "pt": "Latin alphabet with Portuguese accents",
    "es": "Latin alphabet with Spanish accents",
    "ar": "Arabic script (العربية)",
    "bn": "Bengali script (বাংলা)",
    "gu": "Gujarati script (ગુજરાતી)",
    "it": "Latin alphabet with Italian accents",
    "fa": "Persian script (Perso-Arabic, as in فارسی)",
}

# How many earlier turns of the conversation to show Gemini as context.
# 6 = about the last 3 question-and-answer pairs: enough to know what is being
# discussed, small enough to keep each request fast.
HISTORY_TURNS = 6

# Symptoms a GP must never miss. Used to tell Gemini what counts as "urgent".
# Based on common NHS "call 999 / urgent" warning signs. To be checked and
# extended by the team in the glossary step (C1).
URGENT_SYMPTOMS = [
    "chest pain or tightness",
    "difficulty breathing / shortness of breath",
    "signs of stroke (face drooping, arm weakness, slurred speech)",
    "fainting or loss of consciousness",
    "seizure / fit",
    "severe bleeding, or coughing / vomiting blood",
    "severe allergic reaction (swollen lips, tongue or throat)",
    "sudden severe headache ('worst ever')",
    "thoughts of suicide or self-harm",
    "high fever with stiff neck, rash that doesn't fade, or confusion",
    "severe abdominal pain",
    "pregnancy with bleeding or severe pain",
    "a baby or child who is floppy, unresponsive or not feeding",
]

GLOSSARY_PATH = Path(__file__).parent / "glossary.json"


# ---------------------------------------------------------------- baseline
def baseline_prompt(source_hint: str, target_lang: str) -> str:
    """The simple version: no medical rules, no glossary, no urgent flags."""
    return (
        f"Transcribe the speech in this audio. The speaker is expected to speak "
        f"{LANGUAGES.get(source_hint, source_hint)}. Detect the language actually spoken, "
        f"then translate the transcript into {LANGUAGES[target_lang]}."
    )


# ---------------------------------------------------------------- medical layer
def medical_system_instruction() -> str:
    """Rules for interpreting in a UK GP appointment. Same for every turn."""
    # Our starter list + every term the glossary marks as urgent (no duplicates).
    urgent = list(URGENT_SYMPTOMS)
    for e in load_glossary():
        if e.get("urgent") and e["term"] not in urgent:
            urgent.append(e["term"])
    urgent_list = "\n".join(f"- {s}" for s in urgent)
    return f"""You are a professional medical interpreter in a UK GP (family doctor) appointment.
A patient with limited English and an English-speaking GP are talking through you.
Lives may depend on accuracy. Follow these rules exactly:

0. NEVER INVENT. Transcribe and translate ONLY words you actually hear. Being in a GP
   appointment does NOT mean the audio is about health: never fill gaps with symptoms or
   phrases that are typical in a clinic. A made-up symptom is far more dangerous than
   saying you could not hear. If you cannot make out the speech, set original_text to
   "[inaudible]", translation to "", and speech_clarity to "inaudible".

1. Transcribe exactly what was said, in the original language and script (e.g. Urdu in Urdu script).
2. Translate faithfully, as a professional interpreter would. Keep the first person:
   "I have pain" stays "I have pain", never "The patient says they have pain".
3. Never soften, exaggerate or leave out symptoms. "Very bad pain" must stay "very bad pain".
   Do not add intensity words that were not said: "tight pain" is NOT "severe pain",
   "a bit of pain" is NOT "pain". Translate the exact descriptive word (tight, sharp, dull, mild...).
4. Keep negations exact: "no chest pain" must never become "chest pain".
5. Keep numbers, durations, doses, medicine names and body parts exact
   (e.g. "since 3 days", "500 mg twice a day", "left side").
6. Use standard medical terms the GP will recognise in English (e.g. "shortness of breath"),
   and plain everyday words when translating for the patient.
7. Do not add advice, explanations, diagnoses or answers. Only interpret what was said.
8. If part of the speech is unclear, write [unclear] at that point rather than guessing.
   Be honest about doubt: list in unclear_words every word or short phrase of the transcript
   you are not confident you heard correctly (mumbled, noisy, cut off, or could be a
   similar-sounding word). Copy each exactly as it appears in original_text. Pay special
   attention to words that change the meaning: verbs, negations, numbers, body parts, medicines.
9. Report the language actually spoken as an ISO 639-1 code (e.g. "ur", "pl", "en"),
   even if it is not the expected language.
10. The translation will be read aloud by a voice, so write it as natural spoken language:
   never use slashes or brackets for alternatives (not "pan/pani", not "he/she", not "(a)").
   Choose ONE form. Where a language needs the listener's gender, use clues from the
   conversation (e.g. how the patient refers to themselves); if there are none, choose
   the most natural polite form.
11. Use only the letters of the target language's own alphabet (e.g. Arabic ة and ي,
   not the Persian forms ه and ی, in Arabic text).

Urgent symptoms: if the speaker REPORTS that someone HAS any of the following (or something clearly
as serious), list each one, in short plain English, in urgent_terms. Only list what was actually said.
Do NOT list a symptom that is:
- denied ("no chest pain", "I don't have a fever")
- only asked about in a question ("Do you have chest pain?", "Any difficulty breathing?")
- mentioned as advice or a hypothetical ("call 999 if you get chest pain")
Otherwise return an empty list.
{urgent_list}"""


_glossary_cache: dict = {"mtime": None, "entries": []}


def load_glossary() -> list[dict]:
    """
    The medical glossary (backend/glossary.json, built by tests/build_glossary.py).
    Read once and kept in memory; re-read automatically if the file changes
    (e.g. after a native speaker marks more translations as verified).
    """
    if not GLOSSARY_PATH.exists():
        return []
    mtime = GLOSSARY_PATH.stat().st_mtime
    if _glossary_cache["mtime"] != mtime:
        _glossary_cache["entries"] = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
        _glossary_cache["mtime"] = mtime
    return _glossary_cache["entries"]


def _glossary_block(target_lang: str) -> str:
    """
    Glossary terms for this target language.

    - Translations a native speaker has CHECKED (verified=true) are given as rules.
    - AI-drafted, unchecked translations are only given as SUGGESTIONS (Gemini
      may use a better word if it's clearly more natural). Set
      USE_UNVERIFIED_GLOSSARY=false in .env to leave them out completely.
    - Translating INTO English: the list of standard English GP terms.
    """
    entries = load_glossary()
    if not entries:
        return ""
    if target_lang == "en":
        terms = ", ".join(e["term"] for e in entries)
        return f"\n\nStandard UK GP terms to use in English when they fit what was said: {terms}."

    checked, suggested = [], []
    for e in entries:
        translation = e.get("translations", {}).get(target_lang, "").strip()
        if not translation:
            continue
        line = f"- {e['term']} = {translation}"
        (checked if e.get("verified", {}).get(target_lang) else suggested).append(line)

    block = ""
    if checked:
        block += "\n\nChecked GP terms (verified by a native speaker). Use these translations:\n" + "\n".join(checked)
    if suggested and USE_UNVERIFIED_GLOSSARY:
        block += (
            "\n\nSuggested GP terms (AI-drafted, not yet checked). Use them if they fit what was said, "
            "unless a clearly more natural everyday word is better:\n" + "\n".join(suggested)
        )
    return block


def _script_rule(source_hint: str, target_lang: str) -> str:
    """Tell Gemini exactly which writing system to use for the transcript and the translation."""
    rule = ""
    if source_hint in SCRIPTS:
        rule += (
            f"Write the transcript in {SCRIPTS[source_hint]}, if the speaker is speaking "
            f"{LANGUAGES[source_hint]} as expected. (Spoken Urdu and Hindi sound alike: if Urdu is "
            f"expected, write Urdu script.) If a clearly different language is spoken, use that "
            f"language's own standard script. "
        )
    if target_lang in SCRIPTS:
        rule += f"Write the translation in {SCRIPTS[target_lang]}."
    return rule


def _history_block(history: list[dict] | None) -> str:
    """
    The last few turns of THIS appointment, as context.

    Why: a sentence like "It started two days ago" or "Yes, on the left" only
    makes sense if you know what was asked before. Real interpreters remember
    the conversation, so we give Gemini the same memory.
    Each history item: {"speaker": "doctor"/"patient", "original_text": ..., "translation": ...}
    """
    if not history:
        return ""
    lines = []
    for turn in history[-HISTORY_TURNS:]:
        who = "Doctor" if turn["speaker"] == "doctor" else "Patient"
        lines.append(f'{who}: "{turn["original_text"]}" (translated: "{turn["translation"]}")')
    return (
        "\n\nEarlier in this appointment (for context ONLY: use it to understand the new audio, "
        "e.g. what 'it' refers to or which body part is meant. Do NOT translate it again, and do NOT "
        "add anything to the translation that the speaker didn't say):\n" + "\n".join(lines)
    )


def medical_prompt(
    source_hint: str, target_lang: str, history: list[dict] | None = None, noisy: bool = False
) -> str:
    """The per-turn request: script rules, noise warning, conversation context, and glossary terms."""
    prompt = (
        f"The speaker is expected to speak {LANGUAGES.get(source_hint, source_hint)}. "
        f"Transcribe the audio, detect the language actually spoken, and translate it into "
        f"{LANGUAGES[target_lang]} following your interpreter rules. "
        + _script_rule(source_hint, target_lang)
    )
    if noisy:
        # audio.py measured background noise in this recording.
        prompt += (
            "\n\nWARNING: our audio check measured background noise in this recording. Be extra careful: "
            "only transcribe words you hear clearly, write [unclear] for the rest and list them in "
            "unclear_words. If you can't make out the meaning, return [inaudible]."
        )
    prompt += _history_block(history)
    prompt += _glossary_block(target_lang)
    return prompt
