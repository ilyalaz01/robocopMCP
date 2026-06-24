# PRD — Reporting & Gmail

**Version 1.00.** SPEC §11. Code-ready tonight; live send is Phase 11.

## Background
When all 6 sub-games are valid, the **Cop** agent emails a structured JSON report to the
grader. The email body is **JSON only** (no prose) so the grader's system can parse it.

## Report shapes (exact field names)
**Internal** (`results/report_internal.json`): `group_name`, `students` (`[{id,name}]`),
`github_repo`, `cop_mcp_url`, `thief_mcp_url`, `timezone`, `sub_games` (list), `totals`
`{cop, thief}`.

**Bonus** (`results/report_bonus.json`): `report_type:"bonus_game"`, `groups`
`{group_1, group_2}`, `github_repo_group_1/2`, `mcp_url_group_1_cop/thief`,
`mcp_url_group_2_cop/thief`, `timezone`, `students_group_1/2`, `sub_games`,
`totals_by_group`, `bonus_claim`, `mutual_agreement`.

## Gmail client
Google Gmail API, OAuth (token-based — `google-api-installation-guide.md`). The send call
goes **through the ApiGatekeeper**. Body = base64-encoded JSON-only message.

## Dry-run (tonight)
`send_report(..., dry_run=True)` writes the exact email body to `results/` and logs it —
proving the pipeline end-to-end **without** sending. Live OAuth send (browser consent +
`credentials.json` + `token.json`) is Phase 11 (with Ilya).

## Edge cases / tests
Schema exactness (every required field present, correct types); dry-run writes a valid
`report_internal.json`; Gmail client with a **mocked** service (no network); email body is
parseable JSON with no extra text.

## Success criteria
Builder tests validate exact schema; mocked-Gmail tests pass; `--dry-run` produces a
correct report + body.
