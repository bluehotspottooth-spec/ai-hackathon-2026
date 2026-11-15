"""
ratelimit.py: stops one person from spamming the app.

Why: once VoiceBridge has a public link, someone who gets the access code
could send hundreds of turns and use up our free ElevenLabs credits
(~400 spoken turns a month) and our Gemini quota. A real appointment is
slow (people take turns talking), so a generous limit never affects normal use.

How: for each visitor (identified by their internet address, IP), we remember
the times of their recent requests. If they made too many in the last few
minutes, we refuse with HTTP 429 "please slow down".

Limits (per visitor):
  - new appointments: 30 per hour   (normal: 1 per appointment)
  - turns:            60 per 5 min  (normal: a few per minute at most)
  (Raised on 15 Nov from 10 and 30: a tester trying several languages, and people sharing
  one Wi-Fi, were locked out for up to an hour. The access code still protects our credits.)

Note: kept in memory, so it resets if the server restarts. That's fine for a prototype.
"""

import threading
import time
from collections import defaultdict, deque

from backend.errors import ServiceError

LIMITS = {
    "session": (30, 60 * 60),  # max 30 new appointments per 60 minutes
    "turn": (60, 5 * 60),      # max 60 turns per 5 minutes
    "clone": (6, 60 * 60),     # max 6 voice copies per hour (each uses one of our ElevenLabs voice slots)
}

_history: dict[tuple[str, str], deque] = defaultdict(deque)
_lock = threading.Lock()


def check(kind: str, visitor: str):
    """Raise ServiceError(429) if this visitor has done `kind` too often recently."""
    max_count, window = LIMITS[kind]
    now = time.time()
    with _lock:
        times = _history[(kind, visitor)]
        while times and now - times[0] > window:  # forget requests older than the window
            times.popleft()
        if len(times) >= max_count:
            wait_min = max(1, round((window - (now - times[0])) / 60))
            raise ServiceError(f"Too many requests. Please wait about {wait_min} minute(s) and try again.", 429)
        times.append(now)


def visitor_id(headers, client_host: str | None) -> str:
    """
    Who is this? Their IP address. On Render the app sits behind a proxy,
    which puts the real address in the 'X-Forwarded-For' header.
    """
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return client_host or "unknown"
