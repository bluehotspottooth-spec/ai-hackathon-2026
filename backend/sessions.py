"""
sessions.py: remembers each appointment while it is happening.

A "session" = one GP appointment. It stores:
  - the two languages (doctor is always English)
  - every turn (who spoke, what was said, the translation)  -> used as HISTORY
    so Gemini understands follow-ups like "it started two days ago"
  - how many turns have been used (limit: 20, to protect our free API credits)

Design decisions:
  - Stored in memory (a Python dict), not a database. Simple, and it means
    nothing about the conversation is kept after the appointment ends or the
    server restarts, which is good for privacy in a prototype.
  - Sessions older than 2 hours are deleted automatically.
  - The access code stops random people who find our public link from using
    up our credits. It is compared with secrets.compare_digest, which takes the
    same time whether the guess is close or not (so it can't be guessed
    letter by letter from timing).
"""

import os
import secrets
import threading
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv

from backend.errors import ServiceError
from backend.prompts import LANGUAGES

load_dotenv()

MAX_TURNS = 20
MAX_AGE_SECONDS = 2 * 60 * 60  # 2 hours

_sessions: dict[str, "Session"] = {}
_lock = threading.Lock()  # several people can use the app at once; the lock stops them clashing


@dataclass
class Session:
    id: str
    doctor_lang: str
    patient_lang: str
    created_at: float = field(default_factory=time.time)
    turns: list[dict] = field(default_factory=list)
    voices: dict = field(default_factory=dict)  # for optional voice cloning later

    @property
    def turns_left(self) -> int:
        return MAX_TURNS - len(self.turns)


def _remove_old_sessions():
    now = time.time()
    for sid in [s.id for s in _sessions.values() if now - s.created_at > MAX_AGE_SECONDS]:
        del _sessions[sid]


def create_session(access_code: str, doctor_lang: str, patient_lang: str) -> Session:
    expected = os.getenv("ACCESS_CODE", "")
    if not expected or not secrets.compare_digest(access_code.strip(), expected):
        raise ServiceError("That code didn't work. Check with the clinic staff.", 401)
    if doctor_lang != "en":
        raise ServiceError("The doctor's language must be English.", 400)
    if patient_lang not in LANGUAGES or patient_lang == "en":
        raise ServiceError("Please choose one of the supported patient languages.", 400)

    session = Session(id=secrets.token_urlsafe(12), doctor_lang=doctor_lang, patient_lang=patient_lang)
    with _lock:
        _remove_old_sessions()
        _sessions[session.id] = session
    return session


def get_session(session_id: str) -> Session:
    with _lock:
        session = _sessions.get(session_id)
    if session is None:
        raise ServiceError("This appointment has ended or doesn't exist. Please start a new one.", 404)
    return session


def check_turn_allowed(session: Session):
    if session.turns_left <= 0:
        raise ServiceError(
            f"This appointment has reached its {MAX_TURNS}-turn limit. Please end it and start a new one.", 429
        )


def add_turn(session: Session, turn: dict):
    """Save a completed turn. Only successful translations count towards the limit."""
    with _lock:
        session.turns.append(turn)


def history(session: Session) -> list[dict]:
    """Earlier turns, in the format pipeline.translate_audio(history=...) expects."""
    return [
        {"speaker": t["speaker"], "original_text": t["original_text"], "translation": t["translation"]}
        for t in session.turns
    ]


def end_session(session_id: str) -> Session:
    """Delete the appointment and everything said in it."""
    with _lock:
        session = _sessions.pop(session_id, None)
    if session is None:
        raise ServiceError("This appointment has already ended.", 404)
    return session
