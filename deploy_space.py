"""
deploy_space.py: builds the folder we push to our Hugging Face Space.

Why a separate folder? Hugging Face only needs the app (backend/, frontend/,
Dockerfile, requirements.txt), and it REJECTS pushes containing binary files
like .mp3 or .docx, which our GitHub repo has in docs/ and tests/. So we copy
just the app into ../voicebridge-space (a separate Git repo linked to the Space).

What it does, each time you run it:
  1. Replaces the app files in ../voicebridge-space with fresh copies.
  2. Switches the frontend to the real backend (USE_MOCK = false) IN THE COPY ONLY.
     The GitHub version stays in demo mode, so double-clicking it still works.
  3. Writes the Space's README.md: Hugging Face reads its settings from the top
     (sdk: docker, app_port: 7860).
API keys are NOT copied (.env stays on this laptop). The Space gets them from
its Settings -> Variables and secrets.

Run it (from the voicebridge folder):
    .venv\\Scripts\\python deploy_space.py
then, in ..\\voicebridge-space:
    git add -A
    git commit -m "Deploy"
    git push
"""

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPACE = HERE.parent / "voicebridge-space"
GITHUB = "https://github.com/bluehotspottooth-spec/ai-hackathon-2026"

# What the app needs. (frontend/old_mockup and frontend/README.md are for the team, not the app.)
COPY_FILES = ["Dockerfile", ".dockerignore", "requirements.txt"]
COPY_DIRS = {"backend": shutil.ignore_patterns("__pycache__", "*.pyc")}
FRONTEND_FILES = ["voicebridge_FINAL.html", "logo.svg"]

README = f"""---
title: VoiceBridge
emoji: 🗣️
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
short_description: Live voice translator for UK GP appointments
---

# VoiceBridge

A live voice translator for UK GP appointments: the doctor speaks English, the patient
speaks one of 11 languages, and each hears the other's words translated and spoken aloud.

Built for the Veritas AI International High School Hackathon 2026.
**Code, tests and write-up:** {GITHUB}

An access code is needed to start an appointment (it protects our API credits).

This project is a prototype and is not medical advice.
"""


def main():
    SPACE.mkdir(exist_ok=True)

    # 1. Remove the old copies of OUR app files (never the Space's .git folder)
    for name in COPY_FILES + list(COPY_DIRS) + ["frontend", "README.md"]:
        target = SPACE / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

    # ...and copy fresh ones in
    for name in COPY_FILES:
        shutil.copy2(HERE / name, SPACE / name)
    for name, ignore in COPY_DIRS.items():
        shutil.copytree(HERE / name, SPACE / name, ignore=ignore)
    (SPACE / "frontend").mkdir()
    for name in FRONTEND_FILES:
        shutil.copy2(HERE / "frontend" / name, SPACE / "frontend" / name)

    # 2. Real backend in the deployed copy
    page = SPACE / "frontend" / "voicebridge_FINAL.html"
    html = page.read_text(encoding="utf-8")
    if "const USE_MOCK = true;" not in html:
        raise SystemExit("Couldn't find 'const USE_MOCK = true;' in the frontend. Stopped, nothing deployed.")
    page.write_text(html.replace("const USE_MOCK = true;", "const USE_MOCK = false;", 1), encoding="utf-8")

    # 3. The Space's README (settings at the top)
    (SPACE / "README.md").write_text(README, encoding="utf-8")

    # Safety check: no secrets in the folder we're about to push
    leaked = [p for p in SPACE.rglob(".env*") if ".git" not in p.parts]
    if leaked:
        raise SystemExit(f"Found {leaked}: secrets must never be pushed. Delete them first.")

    files = sorted(str(p.relative_to(SPACE)) for p in SPACE.rglob("*") if p.is_file() and ".git" not in p.parts)
    print(f"Space folder ready: {SPACE}")
    print("\n".join("  " + f for f in files))
    print("Frontend set to the real backend (USE_MOCK = false) in this copy only.")


if __name__ == "__main__":
    main()
