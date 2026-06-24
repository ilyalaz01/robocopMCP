"""Static board renders (matplotlib) — the submission's "screenshots" (SPEC §13).

No live GUI: each key frame of a sub-game is drawn to a PNG from the per-ply
``state`` events already in the JSONL log. Excluded from coverage because it is
pure rendering with no business logic.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend — no display needed
import matplotlib.pyplot as plt  # noqa: E402


def _states_for(jsonl_path: Path, session_id: str) -> list[dict]:
    """All per-ply state snapshots logged for one sub-game session."""
    out = []
    for line in Path(jsonl_path).read_text().splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        if ev.get("event") == "state" and ev.get("session_id") == session_id:
            out.append(ev)
    return out


def render_frame(state: dict, width: int, height: int, title: str, path: Path) -> None:
    """Draw one board frame (cop, thief, barriers) to a PNG."""
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_xticks(range(width))
    ax.set_yticks(range(height))
    ax.grid(True, color="#cccccc")
    ax.set_aspect("equal")
    for bx, by in state.get("barriers", []):
        ax.add_patch(plt.Rectangle((bx - 0.5, by - 0.5), 1, 1, color="#333333"))
    cx, cy = state["cop"]
    tx, ty = state["thief"]
    ax.scatter([cx], [cy], s=420, c="#1f77b4", marker="o", label="Cop", zorder=3)
    ax.scatter([tx], [ty], s=420, c="#d62728", marker="*", label="Thief", zorder=3)
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def render_match(jsonl_path: Path, match_id: str, num_games: int, width: int,
                 height: int, out_dir: Path) -> list[Path]:
    """Render the first and last frame of each sub-game; return the PNG paths."""
    out = Path(out_dir) / match_id
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i in range(num_games):
        states = _states_for(jsonl_path, f"{match_id}-sg{i}")
        if not states:
            continue
        for label, state in (("start", states[0]), ("end", states[-1])):
            path = out / f"sg{i}_{label}.png"
            render_frame(state, width, height, f"{match_id} sub-game {i} ({label})", path)
            paths.append(path)
    return paths
