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
"""

import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_v4_turbo")
OUTPUT_FORMAT = "mp3_44100_64"  # good speech quality, small file (~8 KB per second)

# Whose words are being spoken -> which stock voice speaks them.
VOICES = {
    "patient": "Xb7hH8MSUJpSbSDYk0k2",  # Alice: patient's words, in English, for the doctor
    "doctor": "onwK4e9ZLuTAKqWW03F9",   # Daniel: doctor's words, in the patient's language
}

_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


class VoiceError(RuntimeError):
    """Speech generation failed. The app can still show the text translation."""


def speak(text: str, language: str, speaker: str = "doctor", voice_id: str | None = None) -> bytes:
    """
    Turn text into MP3 audio bytes.

    text:      what to say (the translation)
    language:  ISO 639-1 code of the text, e.g. "ur", "en"
    speaker:   whose words these are ("doctor" or "patient"); picks the voice
    voice_id:  optional override (e.g. a cloned voice, if we add that later)
    """
    if not text.strip():
        raise VoiceError("Nothing to say.")
    # Safety net: a slash is read out loud as the word "slash" (we found this in
    # Polish: "pani/pan" was spoken as "pani ukośnik pan"). A comma gives a short pause instead.
    spoken_text = text.replace("/", ", ")
    try:
        chunks = _client.text_to_speech.convert(
            voice_id=voice_id or VOICES[speaker],
            text=spoken_text,
            model_id=MODEL,
            language_code=language,
            output_format=OUTPUT_FORMAT,
        )
        # The SDK streams the audio back in pieces; join them into one MP3.
        return b"".join(chunks)
    except Exception as e:
        print(f"[voice] ElevenLabs error ({type(e).__name__}): {e}")
        raise VoiceError("The spoken translation isn't available right now.") from e


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
