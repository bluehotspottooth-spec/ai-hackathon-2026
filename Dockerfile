# Dockerfile: the "recipe" Hugging Face follows to run VoiceBridge online.
# Docker builds a small, clean computer ("container") with exactly what we need,
# so the app runs the same on Hugging Face as on our laptops.
#
# NOT TESTED LOCALLY YET (Docker isn't installed on our laptop). Hugging Face
# builds it for us when we deploy. Any build errors will show in the Space's logs.

# 1. Start from an official, slim Python 3.12 (same version we developed with)
FROM python:3.12-slim

# 2. Install ffmpeg: pydub needs it to read browser/phone recordings (webm, m4a...)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 3. Hugging Face runs apps as a normal user (id 1000), not as the all-powerful "root"
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1
WORKDIR /home/user/app

# 4. Install our Python packages first (Docker caches this step, so code changes rebuild faster)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 5. Copy in only the code the app needs (tests, data and docs stay out; see .dockerignore)
COPY --chown=user backend ./backend
COPY --chown=user frontend ./frontend

# 6. Hugging Face Spaces expect the app on port 7860.
#    API keys are NOT in the image: they come from the Space's "Secrets" settings
#    as environment variables (GEMINI_API_KEY, ELEVENLABS_API_KEY, ACCESS_CODE).
EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
