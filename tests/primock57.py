"""
primock57.py: read the PriMock57 transcripts (Praat TextGrid files).

Each consultation has two files, e.g.
  day1_consultation01_doctor.TextGrid
  day1_consultation01_patient.TextGrid
Each file lists what that person said, with start/end times. We merge the two
into one conversation in time order, and remove the transcribers' markup tags
like <UNSURE>...</UNSURE> or <INAUDIBLE/>.

Dataset: PriMock57, Babylon Health (CC BY 4.0), github.com/babylonhealth/primock57
"""

import re
from pathlib import Path

TRANSCRIPTS = Path(__file__).resolve().parent.parent / "data" / "primock57" / "transcripts"

_INTERVAL = re.compile(r'xmin = ([\d.]+)\s*\n\s*xmax = ([\d.]+)\s*\n\s*text = "(.*?)"\s*\n', re.S)


def consultation_ids() -> list[str]:
    """All consultation IDs, e.g. 'day1_consultation01' (57 in total)."""
    return sorted({p.name.rsplit("_", 1)[0] for p in TRANSCRIPTS.glob("*_doctor.TextGrid")})


def _clean(text: str) -> str:
    text = text.replace('""', '"')                # TextGrid escapes quotes by doubling them
    text = re.sub(r"<[^>]+>", " ", text)          # remove markup tags but keep the words inside
    return re.sub(r"\s+", " ", text).strip()


def utterances(cid: str) -> list[dict]:
    """Everything said in one consultation, in time order: [{start, speaker, text}, ...]."""
    lines = []
    for speaker in ("doctor", "patient"):
        raw = (TRANSCRIPTS / f"{cid}_{speaker}.TextGrid").read_text(encoding="utf-8")
        for start, _end, text in _INTERVAL.findall(raw):
            text = _clean(text)
            if text:
                lines.append({"start": float(start), "speaker": speaker, "text": text})
    return sorted(lines, key=lambda u: u["start"])


def as_text(cid: str) -> str:
    """The whole consultation as a readable script: 'Doctor: ...' / 'Patient: ...'."""
    return "\n".join(f"{u['speaker'].title()}: {u['text']}" for u in utterances(cid))
