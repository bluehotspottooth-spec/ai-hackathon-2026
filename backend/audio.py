"""
audio.py: turn any recording into clean audio that Gemini can understand.

Why we need this:
- Browsers and phones record in different formats (Chrome: webm/opus,
  iPhone: m4a/mp4, Gradio: usually wav). Gemini does not accept webm.
- So we convert EVERYTHING into one standard format: WAV, 16 kHz, mono.
  * WAV is accepted by Gemini.
  * 16 kHz mono is plenty for speech (Gemini down-samples audio anyway),
    and it keeps files small: about 32 KB per second.
- We also reject recordings that are empty, too short, too long or silent,
  with a clear message, BEFORE spending money on an API call.

pydub does the work, and uses ffmpeg (installed on our computer, and in the
Docker image later) underneath to read all the different formats.
"""

import io

from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

# --- Settings (easy to change in one place) ---
SAMPLE_RATE = 16_000      # samples per second; 16 kHz is standard for speech
MIN_SECONDS = 0.5         # shorter than this is almost certainly an accidental tap
MAX_SECONDS = 60.0        # one turn of a conversation; longer = probably forgot to stop
SILENCE_DBFS = -50.0      # loudness threshold; quieter than this = nothing was said


class AudioError(ValueError):
    """A problem with the recording. The message is safe to show the user."""


def convert_to_wav(audio_bytes: bytes) -> tuple[bytes, float]:
    """
    Convert a recording (webm, m4a, mp3, wav, ogg...) to 16 kHz mono WAV.

    Returns (wav_bytes, duration_in_seconds).
    Raises AudioError if the recording is empty, unreadable, too short,
    too long or silent.
    """
    # 1. Empty upload (e.g. the mic never started)
    if not audio_bytes:
        raise AudioError("The recording is empty. Please try again.")

    # 2. Decode it. We don't tell ffmpeg the format: it detects it itself
    #    from the file's contents, so any format works.
    try:
        sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
    except (CouldntDecodeError, IndexError, OSError):
        raise AudioError("We couldn't read that recording. Please try again.")

    # 3. Check length (pydub measures in milliseconds)
    duration = len(sound) / 1000
    if duration < MIN_SECONDS:
        raise AudioError("That recording was too short. Hold the button while you speak.")
    if duration > MAX_SECONDS:
        raise AudioError(f"That recording was longer than {int(MAX_SECONDS)} seconds. Please say it in shorter parts.")

    # 4. Check it isn't silent. dBFS = loudness; 0 is the maximum, more negative = quieter.
    #    sound.max_dBFS is the loudest moment in the clip.
    if sound.max_dBFS < SILENCE_DBFS:
        raise AudioError("We couldn't hear anything. Check your microphone and try again.")

    # 5. Standardise: one channel (mono), 16 kHz, 16-bit samples
    sound = sound.set_channels(1).set_frame_rate(SAMPLE_RATE).set_sample_width(2)

    # 6. Export as WAV into memory (no temporary files to clean up)
    out = io.BytesIO()
    sound.export(out, format="wav")
    return out.getvalue(), round(duration, 2)


# Quick manual test: python -m backend.audio path/to/recording.webm
if __name__ == "__main__":
    import sys

    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()
    try:
        wav, secs = convert_to_wav(data)
        print(f"OK: {path} -> {len(wav):,} bytes of WAV, {secs} seconds")
    except AudioError as e:
        print(f"Rejected: {path} -> {e}")
