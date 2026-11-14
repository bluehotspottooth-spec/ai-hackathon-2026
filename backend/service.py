"""
service.py: the 4 things the app can do, joined together in one place.

  create_session(access_code, doctor_lang, patient_lang)
  run_turn(session_id, speaker, audio)        <- one person speaks
  get_summary(session_id)
  end_session(session_id)

Both frontends call these (the HTML app through the /api endpoints in main.py,
a Gradio app directly), so the logic is written once. Every function returns a
plain dict with exactly the fields in the API contract (CLAUDE.md section 6),
or raises ServiceError with a friendly message.

What one turn does:
  1. check the appointment exists and has turns left        (sessions.py)
  2. clean up the recording + noise check                   (audio.py)
  3. Gemini: transcribe + translate, with the conversation
     history as context                                     (pipeline.py)
  4. speak the translation (ElevenLabs -> backup -> text)   (voice.py)
  5. save the turn so the next one has context              (sessions.py)
"""

import base64
import time
from pathlib import Path

from pydantic import BaseModel

from backend import pipeline, sessions, voice
from backend.audio import AudioError, convert_to_wav
from backend.errors import ServiceError
from backend.prompts import LANGUAGES

__all__ = ["ServiceError", "create_session", "run_turn", "get_summary", "end_session"]


def create_session(access_code: str, doctor_lang: str, patient_lang: str) -> dict:
    s = sessions.create_session(access_code, doctor_lang, patient_lang)
    return {"session_id": s.id, "turns_left": s.turns_left}


def run_turn(session_id: str, speaker: str, audio: bytes | str) -> dict:
    """
    One person speaks. `audio` is the recording's bytes (HTML app) or a file
    path (Gradio gives a path).
    """
    if speaker not in ("doctor", "patient"):
        raise ServiceError("Speaker must be 'doctor' or 'patient'.", 400)
    session = sessions.get_session(session_id)
    sessions.check_turn_allowed(session)

    # Who speaks decides the direction.
    if speaker == "patient":
        source, target = session.patient_lang, "en"
    else:
        source, target = "en", session.patient_lang

    t_start = time.perf_counter()

    # 1. Audio: convert + checks (empty, too short/long, silent, too noisy)
    audio_bytes = Path(audio).read_bytes() if isinstance(audio, str) else audio
    try:
        wav, _seconds, noisy = convert_to_wav(audio_bytes)
    except AudioError as e:
        raise ServiceError(str(e), 400)
    t_converted = time.perf_counter()

    # 2. Translate, with the earlier turns as context
    try:
        result = pipeline.translate_audio(
            wav, source, target, history=sessions.history(session), noisy=noisy
        )
    except pipeline.PipelineError as e:
        raise ServiceError(str(e), 502)
    t_translated = time.perf_counter()

    # 3. Speak it (unless nothing could be heard)
    audio_b64 = ""
    inaudible = result["speech_clarity"] == "inaudible" or not result["translation"]
    if not inaudible:
        try:
            spoken = voice.speak_detailed(result["translation"], target, speaker)
            audio_b64 = base64.b64encode(spoken["mp3"]).decode("ascii")
        except voice.VoiceError:
            audio_b64 = ""  # the screen shows the text; the turn still works
    t_spoken = time.perf_counter()

    # 4. Save the turn (inaudible turns don't count towards the limit)
    if not inaudible:
        sessions.add_turn(session, {
            "speaker": speaker,
            "original_text": result["original_text"],
            "translation": result["translation"],
            "detected_language": result["detected_language"],
            "urgent_terms": result["urgent_terms"],
            "time": time.time(),
        })

    return {
        "original_text": result["original_text"],
        "detected_language": result["detected_language"],
        "target_language": target,
        "translation": result["translation"],
        "urgent_terms": result["urgent_terms"],
        "unclear_words": result["unclear_words"],
        "speech_clarity": result["speech_clarity"],
        "noisy": noisy,
        "audio_base64": audio_b64,
        "timings": {
            "convert": round(t_converted - t_start, 2),
            "translate": round(t_translated - t_converted, 2),
            "speak": round(t_spoken - t_translated, 2),
            "total": round(t_spoken - t_start, 2),
        },
        "turns_left": session.turns_left,
    }


class _Summary(BaseModel):
    summary_en: str
    summary_patient_lang: str


def get_summary(session_id: str) -> dict:
    """A short summary of the appointment, in English (for the GP) and in the patient's language."""
    session = sessions.get_session(session_id)
    if not session.turns:
        raise ServiceError("Nothing has been said yet, so there's nothing to summarise.", 400)
    lang = LANGUAGES[session.patient_lang]
    transcript = "\n".join(
        f"{'Doctor' if t['speaker'] == 'doctor' else 'Patient'}: "
        f"{t['original_text'] if t['speaker'] == 'doctor' else t['translation']}"
        for t in session.turns
    )
    urgent = sorted({u for t in session.turns for u in t["urgent_terms"]})
    prompt = (
        "Summarise this GP appointment, which was interpreted between English and "
        f"{lang}. Write 3-6 short bullet points covering: the patient's main problems and how long they've had "
        "them, important answers (e.g. allergies, medicines), and what the doctor advised or will do next.\n"
        "Rules: only use what was actually said; do NOT add a diagnosis, advice or anything else; keep numbers, "
        "doses and medicine names exact. Keep the speaker's own descriptive words in BOTH languages: never add "
        "intensity words that weren't said (a 'tight pain' is NOT a 'severe pain'). "
        + (f"Mention clearly that these urgent symptoms were reported: {', '.join(urgent)}. " if urgent else "")
        + f"Give summary_en in English and summary_patient_lang as the same summary in simple {lang}.\n\n"
        f"Conversation (in English):\n{transcript}"
    )
    try:
        r = pipeline._client.interactions.create(
            model=pipeline.MODEL,
            input=prompt,
            response_format={"type": "text", "mime_type": "application/json", "schema": _Summary.model_json_schema()},
            generation_config={"thinking_level": "minimal"},
            timeout=30,
        )
        s = _Summary.model_validate_json(r.output_text)
    except Exception as e:
        print(f"[service] summary failed ({type(e).__name__}): {e}")
        raise ServiceError("We couldn't make the summary right now. Please try again.", 502)
    return {"summary_en": s.summary_en.strip(), "summary_patient_lang": s.summary_patient_lang.strip()}


def end_session(session_id: str) -> dict:
    """End the appointment: everything said in it is deleted."""
    sessions.end_session(session_id)
    # (If we add voice cloning, cloned voices are deleted here too.)
    return {"ended": True}
