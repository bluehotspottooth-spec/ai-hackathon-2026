"""
voice.py: turns the translated text into speech (MP3) with ElevenLabs.

Model: eleven_v4_turbo
  ElevenLabs' docs (checked 14 Nov 2026) list it as supporting ALL 11 of our
  patient languages + English, with "ultra-low latency" (~100 ms median).
  Older models (eleven_multilingual_v2, eleven_flash_v2_5) do NOT support
  Urdu, Panjabi, Bengali, Gujarati or Persian, so half our users would have
  had no audio.

Voices (ElevenLabs stock voices, not cloned from real people):
  - "Alice" (clear, British) speaks the PATIENT's words to the doctor, in English.
  - "Daniel" (steady, British) speaks the DOCTOR's words to the patient.
  Two different voices make it obvious which direction a translation is going.

We pass the language code too, because Urdu, Persian and Arabic share an
alphabet: the code tells the voice how to pronounce the words.

BACKUP VOICE (Gemini text-to-speech, model gemini-3.8-flash-lite-tts):
  If ElevenLabs fails for ANY reason (free credits used up, service down,
  network problem), we automatically try Gemini's own voice instead, so the
  doctor or patient still hears the translation. Google's docs list 10 of our
  11 languages for it (Urdu is not listed; we tested it, see ERRORS_AND_FIXES).
  If both fail, the app still shows the text translation on screen.
"""

import base64
import io
import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from google import genai
from pydub import AudioSegment

load_dotenv()

MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_v4_turbo")
OUTPUT_FORMAT = "mp3_44100_64"  # good speech quality, small file (~8 KB per second)

# Whose words are being spoken -> which stock voice speaks them.
VOICES = {
    "patient": "Xb7hH8MSUJpSbSDYk0k2",  # Alice: patient's words, in English, for the doctor
    "doctor": "onwK4e9ZLuTAKqWW03F9",   # Daniel: doctor's words, in the patient's language
}

# Backup voice settings (Gemini TTS). Two different voices again, one per direction.
BACKUP_MODEL = os.getenv("BACKUP_TTS_MODEL", "gemini-3.8-flash-lite-tts")
BACKUP_VOICES = {"patient": "Sulafat", "doctor": "Charon"}  # Sulafat = warm, Charon = informative

# Hard stop for the backup voice. Google's own time limit was NOT enforced for
# voice requests (one hung for 90+ s), so we run the request on a separate
# "worker" thread and simply stop waiting after this many seconds. The user
# then gets the text translation without audio, instead of a frozen app.
BACKUP_HARD_STOP_SECONDS = 15
_backup_worker = ThreadPoolExecutor(max_workers=4)

# For testing the backup on purpose: set VOICE_PROVIDER=gemini in .env
VOICE_PROVIDER = os.getenv("VOICE_PROVIDER", "elevenlabs")

_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
# Gemini's voice models are only reachable through the BETA version of the API
# ("v1beta"): with the default version they return "model not found" (we hit this,
# see ERRORS_AND_FIXES). Google's own speech example uses v1beta too.
_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options={"api_version": "v1beta"})


class VoiceError(RuntimeError):
    """Speech generation failed. The app can still show the text translation."""


def _elevenlabs(text: str, language: str, speaker: str, voice_id: str | None) -> bytes:
    chunks = _client.text_to_speech.convert(
        voice_id=voice_id or VOICES[speaker],
        text=text,
        model_id=MODEL,
        language_code=language,
        output_format=OUTPUT_FORMAT,
    )
    # The SDK streams the audio back in pieces; join them into one MP3.
    return b"".join(chunks)


def _gemini_tts(text: str, speaker: str) -> bytes:
    """Backup voice. Gemini returns WAV; we convert it to MP3 so the app only ever handles one format."""
    interaction = _gemini.interactions.create(
        model=BACKUP_MODEL,
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{"type": "speech_metadata", "style": "calm, clear and kind, like a medical interpreter"}],
            }],
        }],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": BACKUP_VOICES[speaker]}]},
        timeout=20,  # we once saw 54 s; better to show text only than keep people waiting
    )
    wav = base64.b64decode(interaction.output_audio.data)
    out = io.BytesIO()
    AudioSegment.from_file(io.BytesIO(wav)).export(out, format="mp3", bitrate="64k")
    return out.getvalue()


def speak_detailed(text: str, language: str, speaker: str = "doctor", voice_id: str | None = None) -> dict:
    """
    Turn text into MP3 audio, trying ElevenLabs first and Gemini as backup.
    Returns {"mp3": bytes, "provider": "elevenlabs" or "gemini"}.
    Raises VoiceError only if BOTH fail.
    """
    if not text.strip():
        raise VoiceError("Nothing to say.")
    # Safety net: a slash is read out loud as the word "slash" (we found this in
    # Polish: "pani/pan" was spoken as "pani ukośnik pan"). A comma gives a short pause instead.
    spoken_text = text.replace("/", ", ")

    if VOICE_PROVIDER != "gemini":
        if voice_id:  # a cloned voice: if it fails, the stock voice below takes over
            try:
                return {"mp3": _elevenlabs(spoken_text, language, speaker, voice_id), "provider": "elevenlabs-clone"}
            except Exception as e:
                print(f"[voice] Cloned voice failed ({type(e).__name__}): {e}. Using the stock voice.")
        try:
            return {"mp3": _elevenlabs(spoken_text, language, speaker, None), "provider": "elevenlabs"}
        except Exception as e:
            print(f"[voice] ElevenLabs failed ({type(e).__name__}): {e}. Trying backup voice.")
    try:
        # Start the backup voice on a worker thread, then wait at most 15 s for it.
        job = _backup_worker.submit(_gemini_tts, spoken_text, speaker)
        return {"mp3": job.result(timeout=BACKUP_HARD_STOP_SECONDS), "provider": "gemini"}
    except FutureTimeout:
        # Too slow: stop waiting. (The thread finishes on its own; we ignore its result.)
        print(f"[voice] Backup voice took over {BACKUP_HARD_STOP_SECONDS}s, so we gave up. Text only.")
        raise VoiceError("The spoken translation isn't available right now. Please read the text.")
    except Exception as e:
        print(f"[voice] Backup voice failed too ({type(e).__name__}): {e}")
        raise VoiceError("The spoken translation isn't available right now. Please read the text.") from e


def speak(text: str, language: str, speaker: str = "doctor", voice_id: str | None = None) -> bytes:
    """
    Turn text into MP3 audio bytes (ElevenLabs, with Gemini as automatic backup).

    text:      what to say (the translation)
    language:  ISO 639-1 code of the text, e.g. "ur", "en"
    speaker:   whose words these are ("doctor" or "patient"); picks the voice
    voice_id:  optional cloned voice (see clone_voice below)
    """
    return speak_detailed(text, language, speaker, voice_id)["mp3"]


# ---------------------------------------------------------------------------
# OPTIONAL: voice cloning (ElevenLabs Instant Voice Cloning)
#
# With the speaker's consent, ~20-60 s of them talking is turned into a copy of
# their voice. Their translations are then spoken in THEIR OWN voice, which feels
# more natural and makes it obvious who is "speaking".
#
# Rules we follow (hackathon + privacy):
#   - Only our TEAM's voices, and only after they tick the consent box.
#   - Every clone is temporary: deleted when the appointment ends, when the
#     appointment expires (2 h), and any leftovers at server start-up.
#   - Clones get a name starting with CLONE_PREFIX, so we only ever delete OUR
#     temporary clones, never other voices on the ElevenLabs account.
#   - Needs the ElevenLabs Starter plan or above (the Free plan has no cloning)
#     and an API key with the "Voices: write" permission.
# ---------------------------------------------------------------------------
CLONE_PREFIX = "VoiceBridge temp"


def clone_voice(wav: bytes, label: str) -> str:
    """Make a temporary copy of a voice from a WAV recording. Returns the new voice_id."""
    try:
        r = _client.voices.ivc.create(
            name=f"{CLONE_PREFIX} {label}",
            files=[("sample.wav", wav, "audio/wav")],
            description="Temporary clone for one VoiceBridge appointment, made with consent. Auto-deleted.",
            # Must be sent: if left out, this SDK version sends an invalid value and
            # ElevenLabs answers "Labels must be serialized dictionary object" (ERRORS_AND_FIXES #39).
            labels={},
        )
        return r.voice_id
    except Exception as e:
        print(f"[voice] Cloning failed ({type(e).__name__}): {e}")
        raise VoiceError("We couldn't copy the voice right now, so the standard voice will be used.") from e


def delete_voice(voice_id: str) -> bool:
    """Delete a cloned voice. Returns True if it worked (never raises: ending must always work)."""
    try:
        _client.voices.delete(voice_id)
        return True
    except Exception as e:
        print(f"[voice] Couldn't delete cloned voice {voice_id} ({type(e).__name__}): {e}")
        return False


def delete_leftover_clones() -> int:
    """Delete temporary clones left behind (e.g. if the server restarted mid-appointment)."""
    try:
        found = _client.voices.search(search=CLONE_PREFIX, page_size=100).voices
    except Exception as e:
        print(f"[voice] Couldn't check for leftover clones ({type(e).__name__}): {e}")
        return 0
    return sum(delete_voice(v.voice_id) for v in found if (v.name or "").startswith(CLONE_PREFIX))


def credits_left() -> int | None:
    """How many ElevenLabs credits remain this month (useful during testing)."""
    try:
        sub = _client.user.subscription.get()
        return sub.character_limit - sub.character_count
    except Exception:
        return None


# Milestone 2 test: python -m backend.voice
#   generates an Urdu and a Polish sentence and saves them as MP3 files.
if __name__ == "__main__":
    import time
    from pathlib import Path

    out_dir = Path("tests/results/milestone2")
    out_dir.mkdir(parents=True, exist_ok=True)
    samples = [
        ("ur", "doctor", "آپ کو یہ درد کب سے ہے؟ کیا سانس لینے میں تکلیف ہوتی ہے؟"),
        ("pl", "doctor", "Od kiedy ma Pan ten ból? Czy ma Pan trudności z oddychaniem?"),
        ("en", "patient", "I have had chest pain since yesterday, and I get short of breath on the stairs."),
    ]
    before = credits_left()
    for lang, speaker, text in samples:
        start = time.perf_counter()
        mp3 = speak(text, lang, speaker)
        secs = time.perf_counter() - start
        path = out_dir / f"{lang}_{speaker}.mp3"
        path.write_bytes(mp3)
        print(f"{lang} ({speaker} voice): {len(mp3):,} bytes in {secs:.2f}s -> {path}")
    after = credits_left()
    if before is not None and after is not None:
        print(f"Credits used: {before - after} | left this month: {after}")
