"""Generate full submission artifacts for a profile: a real negotiated Haiku series.

Reproducible end-to-end run (negotiation → 6 sub-games → transcripts → board PNGs
→ run summary → dry-run report). Everything goes through the SDK; this script is
pure orchestration of SDK calls.

Usage::

    uv run python scripts/run_demo.py            # solo profile (partial + deception)
    uv run python scripts/run_demo.py bonus      # bonus profile (full + truthful)
"""

from __future__ import annotations

import json
import sys

from robocop_mcp.agents.anthropic_client import build_language_engine
from robocop_mcp.orchestrator.negotiation import make_llm_speaker
from robocop_mcp.reporting.render import render_match
from robocop_mcp.reporting.summary import build_run_summary, summary_markdown
from robocop_mcp.reporting.transcript import write_transcript
from robocop_mcp.sdk.sdk import MarlSDK
from robocop_mcp.shared.config import ConfigManager


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "solo"
    match = f"{profile}_demo"
    sdk = MarlSDK(config=ConfigManager(profile=profile))
    results = sdk.cfg.root / "results"
    engine = build_language_engine(sdk.cfg, sdk.jsonl)

    # 1) Negotiate the rules in natural language (bonus converges on SHARED_RULES).
    sdk.negotiate(stance="agree", match_id=match, speaker=make_llm_speaker(engine))

    # 2) Play the full series: message = Haiku, move = Q-table suggestion.
    series = sdk.run_series(decider=sdk.build_llm_decider(), match_id=match)

    # 3) Artifacts: transcript, board PNGs, run summary, dry-run report.
    write_transcript(sdk.jsonl, match, results)
    rules = sdk.rules
    render_match(sdk.jsonl, match, rules.num_games, rules.grid_width, rules.grid_height, results)
    summary = build_run_summary(series, sdk.jsonl)
    out = results / match
    (out / "summary.md").write_text(summary_markdown(summary))
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    sdk.send_report(series, dry_run=True, out_dir=out)

    print(json.dumps({"profile": profile, "match": match, "totals": series.totals,
                      "valid": summary["valid_sub_games"], "cost": summary["cost"]}, indent=2))
    print("artifacts in", out)


if __name__ == "__main__":
    main()
