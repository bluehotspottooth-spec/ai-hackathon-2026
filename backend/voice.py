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
        try:
            return {"mp3": _elevenlabs(spoken_text, language, speaker, voice_id), "provider": "elevenlabs"}
        except Exception as e:
            print(f"[voice] ElevenLabs failed ({type(e).__name__}): {e}. Trying backup voice.")
    try:
        return {"mp3": _gemini_tts(spoken_text, speaker), "provider": "gemini"}
    except Exception as e:
        print(f"[voice] Backup voice failed too ({type(e).__name__}): {e}")
        raise VoiceError("The spoken translation isn't available right now. Please read the text.") from e


def speak(text: str, language: str, speaker: str = "doctor", voice_id: str | None = None) -> bytes:
    """
    Turn text into MP3 audio bytes (ElevenLabs, with Gemini as automatic backup).

    text:      what to say (the translation)
    language:  ISO 639-1 code of the text, e.g. "ur", "en"
    speaker:   whose words these are ("doctor" or "patient"); picks the voice
    voice_id:  optional override (e.g. a cloned voice, if we add that later)
    """
    return speak_detailed(text, language, speaker, voice_id)["mp3"]


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
