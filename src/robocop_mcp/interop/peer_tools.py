"""PeerToolService — the opponent-compatible MCP tool surface (assignment §26).

Exact tool names from their spec, each token-guarded, delegating to a
:class:`MatchSession`. A PlayerAgent is both MCP server (these tools) and MCP
client (it calls the opponent's same-named tools). Names are also discoverable
via ``get_capabilities`` so any opponent can adapt (capability_handshake).
"""

from __future__ import annotations

from .capability_handshake import our_capabilities
from .constants import INTEGRITY_PROMISE
from .game_adapter import ROLE_FROM_STR
from .hashing import ruleset_hash as _compute_ruleset_hash
from .session import MatchSession


class PeerToolService:
    """Implements the peer MCP tools over one match session (token-guarded)."""

    def __init__(self, session: MatchSession, token: str,
                 repo_url: str = "", mcp_urls: dict | None = None, students: list | None = None) -> None:
        self.s = session
        self.token = token
        self._identity = (repo_url, mcp_urls or {}, students or [])

    def _auth(self, token: str) -> dict | None:
        return None if token == self.token else {"ok": False, "error": "unauthorized"}

    # --- pre-game -------------------------------------------------------
    def get_capabilities(self, token: str) -> dict:
        err = self._auth(token)
        if err:
            return err
        repo, urls, students = self._identity
        return {"ok": True, "capabilities": our_capabilities(self.s.our_team, repo, urls, students)}

    def propose_ruleset(self, token: str, ruleset_name: str, ruleset_hash: str) -> dict:
        err = self._auth(token)
        return err or {"ok": True, "our_ruleset_name": "cop-robber-grid-v1",
                       "our_ruleset_hash": _compute_ruleset_hash()}

    def accept_ruleset(self, token: str, ruleset_name: str, ruleset_hash: str) -> dict:
        err = self._auth(token)
        if err:
            return err
        ok = self.s.accept_ruleset(ruleset_name, ruleset_hash)
        return {"ok": ok, "terminal": None if ok else "protocol_failure"}

    def exchange_team_identity(self, token: str, team_name: str, students=None,
                               repo_url: str = "", mcp_urls=None) -> dict:
        err = self._auth(token)
        if err:
            return err
        self.s.set_opponent(team_name)
        return {"ok": True, "team_a": self.s.team_a}

    def commit_nonce(self, token: str, sub_game_index: int, nonce_hash: str) -> dict:
        err = self._auth(token)
        if err:
            return err
        self.s.opp_commitments[sub_game_index] = nonce_hash
        return {"ok": True, "our_commitment": self.s.our_commitment(sub_game_index)}

    def reveal_nonce(self, token: str, sub_game_index: int, nonce: str) -> dict:
        err = self._auth(token)
        if err:
            return err
        ok = self.s.reveal_ok(sub_game_index, nonce)
        return {"ok": ok, "our_nonce": self.s.our_nonces.get(sub_game_index)}

    def confirm_role_schedule(self, token: str, schedule: dict) -> dict:
        return self._auth(token) or {"ok": True, "team_a": self.s.team_a}

    def confirm_integrity_promise(self, token: str, message: str) -> dict:
        err = self._auth(token)
        if err:
            return err
        self.s.integrity_confirmed = True
        return {"ok": True, "promise": INTEGRITY_PROMISE}

    # --- game -----------------------------------------------------------
    def start_sub_game(self, token: str, sub_game_index: int, role: str,
                       initial_positions: dict, seed_data: dict | None = None) -> dict:
        err = self._auth(token)
        if err:
            return err
        t = self.s.agent.translator
        cop = t.coord_to_cell(initial_positions["cop"])
        rob = t.coord_to_cell(initial_positions["robber"])
        from ..domain.models import Position
        self.s.agent.start_sub_game(ROLE_FROM_STR[role], Position(*cop), Position(*rob), self.s.rules)
        return {"ok": True}

    def receive_action_message(self, token: str, sub_game_index: int, round_index: int,
                               actor: str, message: str) -> dict:
        err = self._auth(token)
        if err:
            return err
        res = self.s.agent.observe(message, ROLE_FROM_STR[actor])
        if not res["ack"]:
            return {"ok": False, "retry": True, "reason": "unclear_action"}
        return {"ok": True, "parsed": res["parsed"]["type"], "terminal": res["code"]}

    def request_action_retry(self, token: str, sub_game_index: int, round_index: int,
                             reason: str) -> dict:
        return self._auth(token) or {"ok": True, "reason": reason}

    def confirm_action_parse(self, token: str, sub_game_index: int, round_index: int,
                             parsed_action: dict) -> dict:
        return self._auth(token) or {"ok": True}

    def confirm_sub_game_result(self, token: str, sub_game_index: int, result_hash: str,
                                result_json: dict) -> dict:
        err = self._auth(token)
        if err:
            return err
        ours = next((r for r in self.s.results if r["sub_game_index"] == sub_game_index), None)
        match = bool(ours) and ours["log_hash"] == result_hash
        return {"ok": match, "agree": match}

    # --- reporting ------------------------------------------------------
    def get_sub_game_log(self, token: str, sub_game_index: int) -> dict:
        err = self._auth(token)
        if err:
            return err
        ours = next((r for r in self.s.results if r["sub_game_index"] == sub_game_index), None)
        return {"ok": bool(ours), "log": ours}

    def get_final_report(self, token: str) -> dict:
        return self._auth(token) or {"ok": True, "sub_games": self.s.results}

    def confirm_final_report(self, token: str, report_hash: str) -> dict:
        err = self._auth(token)
        if err:
            return err
        self.s.opponent_report_hash = report_hash
        match = self.s.final_hash is not None and self.s.final_hash == report_hash
        return {"ok": True, "match": match, "our_hash": self.s.final_hash}

    def send_final_report_email(self, token: str, report_json: dict) -> dict:
        # Interop NEVER auto-sends: emailing requires manual confirmation + a hash
        # match (interop.finalize with --send). This tool only acknowledges.
        return self._auth(token) or {"ok": True, "sent": False,
                                     "note": "manual confirmation required (interop.finalize --send)"}
