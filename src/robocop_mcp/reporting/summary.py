"""Run summary + token-cost accounting (SPEC §13, rubric §10).

Mines the JSONL event stream for API token usage and combines it with a series
result into a compact pass/fail + cost summary. Pure functions over already-logged
data, so they are fully unit-testable.
"""

from __future__ import annotations

import json
from pathlib import Path

# Haiku list price (USD per million tokens) — input / output.
HAIKU_RATES = {"input": 1.0, "output": 5.0}


def token_cost(jsonl_path: Path, rates: dict | None = None) -> dict:
    """Sum input/output tokens from ``api_call`` events and price them."""
    rates = rates or HAIKU_RATES
    in_tok = out_tok = calls = 0
    for line in Path(jsonl_path).read_text().splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        if ev.get("event") != "api_call":
            continue
        calls += 1
        in_tok += ev.get("input_tokens") or 0
        out_tok += ev.get("output_tokens") or 0
    cost = in_tok / 1e6 * rates["input"] + out_tok / 1e6 * rates["output"]
    return {"api_calls": calls, "input_tokens": in_tok, "output_tokens": out_tok,
            "cost_usd": round(cost, 6)}


def build_run_summary(series, jsonl_path: Path, rates: dict | None = None) -> dict:
    """Combine per-sub-game outcomes, totals, and token cost into one summary."""
    rows = [
        {"index": sg.index, "outcome": sg.outcome.value, "moves": sg.moves,
         "cop_score": sg.cop_score, "thief_score": sg.thief_score,
         "valid": not sg.void}
        for sg in series.sub_games
    ]
    return {
        "match_id": series.match_id,
        "sub_games": rows,
        "valid_sub_games": sum(1 for r in rows if r["valid"]),
        "totals": series.totals,
        "cost": token_cost(jsonl_path, rates),
    }


def summary_markdown(summary: dict) -> str:
    """Render the run summary as a Markdown table for the README/screenshots."""
    lines = [f"# Run summary — `{summary['match_id']}`", "",
             "| Sub-game | Outcome | Moves | Cop | Thief | Valid |",
             "| --- | --- | --- | --- | --- | --- |"]
    for r in summary["sub_games"]:
        lines.append(f"| {r['index']} | {r['outcome']} | {r['moves']} | "
                     f"{r['cop_score']} | {r['thief_score']} | {'✓' if r['valid'] else '✗'} |")
    c = summary["cost"]
    lines += ["", f"**Totals:** cop {summary['totals']['cop']}, thief {summary['totals']['thief']}",
              f"**Valid sub-games:** {summary['valid_sub_games']}",
              f"**API:** {c['api_calls']} calls, {c['input_tokens']} in / {c['output_tokens']} out "
              f"tokens → **${c['cost_usd']}**"]
    return "\n".join(lines) + "\n"
