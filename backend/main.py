"""
main.py: the web server. It turns service.py's functions into web addresses
(the "doors" the frontend knocks on), exactly as in the API contract:

  POST /api/session   start an appointment          (JSON in, JSON out)
  POST /api/clone     OPTIONAL: copy a speaker's voice, with consent (form with an audio file)
  POST /api/turn      one person speaks              (form with an audio file)
  POST /api/summary   summary of the appointment     (JSON)
  POST /api/end       end + delete the appointment   (JSON)
  GET  /api/health    "is the server up?"            (for deployment checks)

Run it:   .venv\\Scripts\\python -m uvicorn backend.main:app --reload
Then open http://localhost:8000/docs for a test page with buttons for every endpoint.

The frontend is served from the same server (same address), so the browser
needs no special permission (CORS) to call /api.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import ratelimit, service, voice
from backend.errors import ServiceError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB: a 60-second recording is far smaller

# At start-up: delete any temporary cloned voices left over from before a restart
# (sessions live in memory, so a restart forgets them without ending them).
# "lifespan" = code FastAPI runs when the server starts (before "yield") and stops (after).
@asynccontextmanager
async def lifespan(_app):
    removed = voice.delete_leftover_clones()
    if removed:
        print(f"[main] Deleted {removed} leftover cloned voice(s) from before the restart.")
    yield


app = FastAPI(
    lifespan=lifespan,
    title="VoiceBridge API",
    description="Live voice translation for UK GP appointments. "
    "This project is a prototype and is not medical advice.",
    version="0.1",
)


# Any ServiceError becomes {"error": "..."} with the right status code (contract rule).
@app.exception_handler(ServiceError)
async def service_error_handler(_request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status, content={"error": exc.message})


# Anything unexpected: log it for us, but show the user a calm message (never a raw crash).
@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, exc: Exception):
    print(f"[main] Unexpected error ({type(exc).__name__}): {exc}")
    return JSONResponse(status_code=500, content={"error": "Something went wrong on our side. Please try again."})


# ---- request shapes for the JSON endpoints (FastAPI checks them automatically)
class SessionRequest(BaseModel):
    access_code: str
    doctor_lang: str = "en"
    patient_lang: str


class SessionIdRequest(BaseModel):
    session_id: str


# ---- endpoints
# These are plain "def" (not "async def"): FastAPI runs them on a worker thread,
# so one slow Gemini call doesn't freeze the server for other users.
def _visitor(request: Request) -> str:
    return ratelimit.visitor_id(request.headers, request.client.host if request.client else None)


@app.post("/api/session")
def create_session(body: SessionRequest, request: Request):
    ratelimit.check("session", _visitor(request))  # spam protection (see ratelimit.py)
    return service.create_session(body.access_code, body.doctor_lang, body.patient_lang)


@app.post("/api/clone")
def clone(request: Request, session_id: str = Form(...), speaker: str = Form(...),
          consent: bool = Form(...), audio: UploadFile = File(...)):
    ratelimit.check("clone", _visitor(request))  # spam protection (see ratelimit.py)
    data = audio.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ServiceError("That recording is too large. Please keep it under a minute.", 400)
    return service.clone_voice(session_id, speaker, consent, data)


@app.post("/api/turn")
def turn(request: Request, session_id: str = Form(...), speaker: str = Form(...), audio: UploadFile = File(...)):
    ratelimit.check("turn", _visitor(request))  # spam protection (see ratelimit.py)
    data = audio.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ServiceError("That recording is too large. Please keep each turn under a minute.", 400)
    return service.run_turn(session_id, speaker, data)


@app.post("/api/summary")
def summary(body: SessionIdRequest):
    return service.get_summary(body.session_id)


@app.post("/api/end")
def end(body: SessionIdRequest):
    return service.end_session(body.session_id)


@app.get("/api/health")
def health():
    return {"ok": True}


# ---- the website itself
# The whole frontend is one file, frontend/voicebridge_FINAL.html, served at "/".
# Any other files in frontend/ (e.g. a logo) are served by name, e.g. /logo.svg.
# If the file doesn't exist, "/" goes to the /docs test page instead.
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_PAGE = FRONTEND / "voicebridge_FINAL.html"
if FRONTEND_PAGE.exists():
    @app.get("/", include_in_schema=False)
    def frontend_page():
        return FileResponse(FRONTEND_PAGE)

    app.mount("/", StaticFiles(directory=FRONTEND), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/docs")
