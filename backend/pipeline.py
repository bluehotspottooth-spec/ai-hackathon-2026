"""
pipeline.py: the AI core of VoiceBridge.

translate_audio() sends ONE recording to Gemini and gets back, in one call:
  - original_text      what was said, in the original language and script
  - detected_language  which language Gemini heard (ISO code, e.g. "ur")
  - translation        the translation into the other person's language
  - urgent_terms       urgent symptoms mentioned (VoiceBridge mode only)

Why one call instead of "speech-to-text, then translate"?
  Fewer steps = less waiting, and Gemini hears the tone and context of the
  speech while translating, rather than working from text alone.

Why structured JSON output?
  We give Gemini a fixed "form" (a schema) to fill in. That way the answer
  always has exactly these four fields, so our code never has to guess
  where the translation starts in a paragraph of text.

Model: gemini-3.5-flash-lite, with thinking_level="minimal".
  Google's docs (checked 14 Nov 2026) list it as stable and recommended for
  low latency. We measured 4 models on the same 13-second clip (EN -> UR, medical layer):
    gemini-3.5-flash-lite  4.0 s   (both urgent symptoms flagged)
    gemini-3.1-flash-lite  4.7 s
    gemini-4-hydrogen      56-135 s  (good quality, far too slow for a live conversation)
    gemini-3.6-flash       request failed
  A live conversation needs a few seconds, so speed decided it.
  The model can be changed in .env with GEMINI_MODEL to compare others.
"""

import base64
import os
import time
from typing import Literal

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

from backend import prompts

load_dotenv()  # reads GEMINI_API_KEY etc. from the .env file

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Lowest-latency thinking setting for each model family (from Google's docs).
THINKING_LEVEL = {"gemini-4": "low", "gemini-3.5-flash-lite": "minimal"}

# Config flag required by our brief: switch OFF to get the plain baseline.
# Tests change it per call with use_medical_layer=...; the app leaves it on.
USE_MEDICAL_LAYER = os.getenv("USE_MEDICAL_LAYER", "true").lower() == "true"

# Retry once on temporary failures (2 attempts in total).
MAX_ATTEMPTS = 2
RETRY_WAIT_SECONDS = 1.5
# Stop waiting after this many seconds. A normal turn takes 3-4 s, but we saw
# random slow answers of 11, 22 and 54 s. Retrying is usually faster than waiting.
TIMEOUT_SECONDS = 20

# One shared client (it reuses the connection, which is faster).
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class PipelineError(RuntimeError):
    """Gemini failed. The message is safe to show the user."""


class TurnResult(BaseModel):
    """The 'form' Gemini must fill in. Field descriptions guide the model."""

    original_text: str = Field(description="Exact transcript of the speech, in the original language and script.")
    detected_language: str = Field(description="ISO 639-1 code of the language actually spoken, e.g. 'ur', 'pl', 'en'.")
    translation: str = Field(description="The translation into the requested target language.")
    urgent_terms: list[str] = Field(description="Urgent symptoms mentioned, in short plain English. Empty list if none.")
    unclear_words: list[str] = Field(
        description="Words or short phrases from original_text you are NOT confident you heard correctly, "
        "copied exactly as written there. Empty list if you are confident."
    )
    speech_clarity: Literal["clear", "partly_unclear", "inaudible"] = Field(
        description="How clearly you could hear the speech: 'clear', 'partly_unclear' (some words uncertain), "
        "or 'inaudible' (could not make it out; then original_text is '[inaudible]')."
    )


def _thinking_level(model: str) -> str | None:
    for prefix, level in THINKING_LEVEL.items():
        if model.startswith(prefix):
            return level
    return None  # unknown model: use its default


def translate_audio(
    wav_bytes: bytes,
    source_hint: str,
    target_lang: str,
    use_medical_layer: bool | None = None,
    model: str | None = None,
    history: list[dict] | None = None,
    noisy: bool = False,
) -> dict:
    """
    Transcribe + detect language + translate one recording with Gemini.

    wav_bytes:          audio already converted by audio.convert_to_wav()
    source_hint:        language we EXPECT the speaker to use, e.g. "ur"
    target_lang:        language to translate into, e.g. "en"
    use_medical_layer:  True = VoiceBridge (GP rules + urgent flags + glossary),
                        False = plain baseline, None = use the USE_MEDICAL_LAYER flag
    model:              optional override, for comparing models in tests
    history:            earlier turns of this appointment (sessions.py keeps them),
                        e.g. [{"speaker": "doctor", "original_text": ..., "translation": ...}].
                        Only used with the medical layer; the baseline has no memory.
    noisy:              True if audio.py measured background noise; Gemini is warned
                        to be extra careful (medical layer only).
    """
    if use_medical_layer is None:
        use_medical_layer = USE_MEDICAL_LAYER
    model = model or MODEL

    # 1. Choose the instructions: our medical layer, or the plain baseline.
    if use_medical_layer:
        system_instruction = prompts.medical_system_instruction()
        request_text = prompts.medical_prompt(source_hint, target_lang, history, noisy)
    else:
        system_instruction = None
        request_text = prompts.baseline_prompt(source_hint, target_lang)

    # 2. Build the request: our text + the audio (sent as base64 text,
    #    which is how the API carries binary data inside a JSON request).
    request = {
        "model": model,
        "input": [
            {"type": "text", "text": request_text},
            {"type": "audio", "data": base64.b64encode(wav_bytes).decode("ascii"), "mime_type": "audio/wav"},
        ],
        # Ask for JSON that matches our TurnResult form.
        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": TurnResult.model_json_schema(),
        },
    }
    if system_instruction:
        request["system_instruction"] = system_instruction
    level = _thinking_level(model)
    if level:
        request["generation_config"] = {"thinking_level": level}

    # 3. Call Gemini and time it. If it fails (busy server, rate limit, network
    #    blip, or a badly-formed answer), wait a moment and try ONE more time
    #    before giving up, so a temporary hiccup doesn't ruin a turn.
    start = time.perf_counter()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            interaction = _client.interactions.create(**request, timeout=TIMEOUT_SECONDS)
            result = TurnResult.model_validate_json(interaction.output_text)
            break
        except Exception as e:
            print(f"[pipeline] Gemini error on attempt {attempt} ({type(e).__name__}): {e}")
            if attempt == MAX_ATTEMPTS:
                raise PipelineError("The translation service didn't respond properly. Please try again.") from e
            time.sleep(RETRY_WAIT_SECONDS)
    seconds = time.perf_counter() - start

    # 4. The baseline must not flag anything: urgent flags and unclear-word
    #    warnings are part of OUR layer.
    urgent = result.urgent_terms if use_medical_layer else []
    original = result.original_text.strip()
    # Keep only "unclear" words that really appear in the transcript, so the
    # screen can highlight them (the model sometimes paraphrases).
    unclear = [w.strip() for w in result.unclear_words if w.strip() and w.strip() in original] if use_medical_layer else []
    clarity = result.speech_clarity if use_medical_layer else "clear"
    if unclear and clarity == "clear":
        clarity = "partly_unclear"  # keep the two answers consistent

    return {
        "original_text": original,
        "detected_language": result.detected_language.strip().lower(),
        "target_language": target_lang,
        "translation": result.translation.strip(),
        "urgent_terms": urgent,
        "unclear_words": unclear,
        "speech_clarity": clarity,
        "noisy": noisy,
        "translate_seconds": round(seconds, 2),
        "model": model,
        "medical_layer": use_medical_layer,
    }


# Manual test (Milestone 1):
#   python -m backend.pipeline tests/clips/urdu.wav --from ur --to en
#   add --baseline to switch off the medical layer, --model NAME to try another model
if __name__ == "__main__":
    import argparse
    import json

    from backend.audio import convert_to_wav

    p = argparse.ArgumentParser(description="Translate one audio file with Gemini.")
    p.add_argument("file")
    p.add_argument("--from", dest="source", required=True, help="expected language code, e.g. ur")
    p.add_argument("--to", dest="target", default="en", help="target language code (default en)")
    p.add_argument("--baseline", action="store_true", help="switch OFF the medical layer")
    p.add_argument("--model", default=None)
    args = p.parse_args()

    with open(args.file, "rb") as f:
        t0 = time.perf_counter()
        wav, secs, noisy = convert_to_wav(f.read())
        convert_s = time.perf_counter() - t0

    out = translate_audio(wav, args.source, args.target, use_medical_layer=not args.baseline, model=args.model, noisy=noisy)
    out["audio_seconds"] = secs
    out["convert_seconds"] = round(convert_s, 2)
    print(json.dumps(out, ensure_ascii=False, indent=2))
