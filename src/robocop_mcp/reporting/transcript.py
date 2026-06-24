"""Human-readable transcript builder — gold for the grader (SPEC §13).

Reads the JSONL event stream for a match and renders a Markdown transcript: the
negotiation dialogue, then each sub-game's turn-by-turn natural-language messages,
actions, and outcome. Pure file I/O over already-logged events, so it adds no
runtime cost to play.
"""

from __future__ import annotations

import json
from pathlib import Path


def _load(jsonl_path: Path) -> list[dict]:
    """Parse the JSONL event stream into a list of records."""
    lines = Path(jsonl_path).read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _belongs(event: dict, match_id: str) -> bool:
    """True if an event belongs to ``match_id`` (by match_id or session_id prefix)."""
    if event.get("match_id") == match_id:
        return True
    sid = event.get("session_id") or ""
    return sid.startswith(f"{match_id}-")


def render(events: list[dict], match_id: str) -> str:
    """Render the Markdown transcript for ``match_id`` from ``events``."""
    mine = [e for e in events if _belongs(e, match_id)]
    lines = [f"# Match transcript — `{match_id}`", ""]
    for ev in mine:
        kind = ev.get("event")
        if kind == "negotiate_propose" or kind == "negotiate_respond" or kind == "negotiate_confirm":
            lines.append(f"- 🗣️ **{ev.get('role')}** {kind}: rules={ev.get('rules', '')}")
        elif kind == "subgame_start":
            lines += ["", f"## Sub-game {ev.get('index')} — cop@{ev.get('cop')} thief@{ev.get('thief')}", ""]
        elif kind == "turn":
            act = ev.get("direction") or ev.get("action")
            ok = "✓" if ev.get("ok") else "✗"
            lines.append(f"- **{ev.get('role')}**: \"{ev.get('message', '')}\" → {act} {ok}")
        elif kind == "belief":
            lines.append(f"    ↳ _{ev.get('role')} believes opponent is {ev.get('belief')}_")
        elif kind == "subgame_end":
            lines.append(f"- **Outcome:** {ev.get('outcome')} in {ev.get('moves')} moves "
                         f"(cop {ev.get('cop_score')}, thief {ev.get('thief_score')})")
        elif kind == "series_end":
            lines += ["", f"**Series totals:** {ev.get('totals')}"]
    return "\n".join(lines) + "\n"


def write_transcript(jsonl_path: Path, match_id: str, out_dir: Path) -> Path:
    """Write ``results/<match_id>/transcript.md`` and return its path."""
    events = _load(jsonl_path)
    out = Path(out_dir) / match_id
    out.mkdir(parents=True, exist_ok=True)
    path = out / "transcript.md"
    path.write_text(render(events, match_id))
    return path
