# Assignment 6 — Dual AI Agent Cop-and-Robber MCP Game

## 0. Purpose of This Document

This document is the implementation specification for Assignment 6: a dual-agent Cop-and-Robber pursuit game played via MCP servers and natural-language communication.

It combines:

1. the lecturer's explicit assignment requirements;
2. the clarified game rules agreed by our team;
3. the no-central-orchestrator/correspondence-game design decision;
4. the inter-student protocol needed for compatible cross-team play;
5. the reporting, email, configuration, security, and README requirements.

This document is intended to be given to Claude Code and to opponent students so that both sides implement compatible agents.

Before any full game starts, both PlayerAgents must complete the pre-game agreement phase defined in this document.

---

## 1. High-Level Assignment Goal

Build a system that allows two autonomous AI agents to play a dynamic Cop-and-Robber pursuit game on a 2D grid using MCP-based communication and natural-language messages.

The two strategic actors are:

- **Cop**: tries to catch the robber.
- **Robber / Thief**: tries to avoid capture until the move limit expires.

The assignment's main success criterion is not only game strategy. The primary goal is to demonstrate a complete autonomous multi-agent pipeline:

- independent agents;
- MCP-based communication;
- natural-language turn messages;
- local and cloud-capable execution;
- configuration-driven game parameters;
- autonomous result logging and reporting;
- JSON email report to the lecturer;
- optional inter-group bonus games.

The terms **Robber** and **Thief** are synonyms. In protocol fields and logs, use `robber` / `R`; in assignment-compatible report fields, `thief` may also appear.

---

## 2. Architecture Decision: No Central Game Orchestrator

### 2.1 Strategic actors

There are exactly two strategic actors in the game:

1. one PlayerAgent acting as Cop in the current sub-game;
2. one PlayerAgent acting as Robber in the current sub-game.

There is no third strategic actor, referee, judge, or central game engine that decides moves.

### 2.2 Correspondence-game model

The game is implemented as a **two-agent correspondence game**.

Each agent independently maintains:

- the inferred board state;
- the move history;
- the block history;
- legal-action validation;
- score calculation;
- terminal-condition detection;
- the full game log;
- final report JSON.

The agreed rule set, initial positions, public action messages, and both agents' logs are the source of truth.

If the two agents' logs disagree, the game is considered failed/invalid unless the disagreement can be resolved from the public message history.

### 2.3 Infrastructure is allowed, but not as a game referee

A tiny CLI/bootstrapper may exist only to start local processes or provide initial URLs. It must not:

- maintain the authoritative board state;
- validate moves as a central referee;
- decide the winner;
- secretly pass direct coordinate updates after moves;
- make strategic decisions.

Each PlayerAgent must contain its own client logic for calling the opponent's MCP server.

### 2.4 MCP requirement

Each running PlayerAgent instance must be able to communicate via MCP. Practically, a PlayerAgent should be both:

1. an **MCP server**, exposing tools for receiving messages, starting games, exchanging protocol data, and returning logs/reports;
2. an **MCP client**, able to call the opponent's MCP server.

Two passive MCP servers are not enough. At least one side must initiate calls, and both sides must be able to send and receive game messages.

---

## 3. PlayerAgent Requirement

### 3.1 One reusable role-flexible agent implementation

Implement one reusable `PlayerAgent` implementation, not separate cop-only and robber-only systems.

A `PlayerAgent` must be capable of playing both roles:

- as **Cop**, it tries to catch the robber and may place barriers;
- as **Robber**, it tries to avoid capture until the round limit.

The role is assigned per sub-game.

### 3.2 Required PlayerAgent responsibilities

Each PlayerAgent must:

1. run as an independent MCP-capable agent;
2. be able to play either Cop or Robber;
3. participate in the pre-game ruleset agreement protocol;
4. accept only a matching published ruleset hash;
5. agree on deterministic role ordering from team names;
6. participate in commit-reveal random seed generation;
7. maintain its own inferred board state from the initial positions and public action messages;
8. parse opponent natural-language actions;
9. validate legal and illegal actions according to the agreed rules;
10. choose only legal actions for itself;
11. honestly communicate its action in English natural language;
12. never cheat, lie, or intentionally misrepresent the board state or action;
13. admit loss if it has no legal action;
14. never resign voluntarily except when the rules force loss;
15. maintain a full tournament-style log;
16. maintain structured logs for debugging/reporting;
17. calculate sub-game scores and full-game totals;
18. confirm sub-game results with the opponent;
19. confirm final report JSON with the opponent;
20. send the required JSON-only email report to the lecturer.

### 3.3 Suggested class shape

```python
class PlayerAgent:
    def start_match(self, opponent_url: str, team_name: str) -> None: ...
    def negotiate_ruleset(self) -> None: ...
    def agree_role_schedule(self) -> None: ...
    def commit_reveal_seed(self, sub_game_index: int) -> str: ...
    def start_sub_game(self, role: str, initial_state: dict) -> None: ...
    def receive_message(self, message: str) -> None: ...
    def parse_action(self, message: str) -> dict: ...
    def update_inferred_state(self, action: dict) -> None: ...
    def validate_action(self, action: dict) -> bool: ...
    def choose_action(self) -> str: ...
    def send_action(self, action_message: str) -> None: ...
    def detect_terminal_condition(self) -> dict | None: ...
    def produce_sub_game_log(self) -> dict: ...
    def produce_final_report(self) -> dict: ...
    def send_final_report_email(self, report: dict) -> None: ...
```

---

## 4. Game Structure

### 4.1 Sub-game

A **sub-game** is one pursuit round between one Cop and one Robber.

Each sub-game has:

- one role-flexible PlayerAgent currently assigned as Cop;
- one role-flexible PlayerAgent currently assigned as Robber;
- one rectangular grid;
- at most 25 full rounds;
- at most 5 cop-placed blocks/barriers.

A sub-game ends when one of the terminal conditions in Section 11 occurs.

### 4.2 Full game

A full game consists of **6 valid sub-games**.

Sub-game results are accumulated into the final score.

Each team/agent should play 3 sub-games as Cop and 3 sub-games as Robber.

### 4.3 Technical failures

If a sub-game fails because of a true technical failure, it is canceled and must be rerun until 6 valid sub-games are completed.

Examples of technical failure:

- MCP server process crash;
- network failure;
- unrecoverable API failure;
- infrastructure outage.

Do **not** classify ordinary game losses as technical failure.

The following are game-rule losses, not technical failures:

- illegal move;
- illegal block placement;
- invalid/unclear action after retry;
- timeout/no response after retry;
- no legal move/action.

---

## 5. Pre-game Agreement and Limited Negotiation

Before the first sub-game starts, both PlayerAgents must complete a short pre-game agreement phase.

The purpose of this phase is to confirm that both PlayerAgents will play the same game under the same rules. This phase is **not** a free-form negotiation that may silently change the official ruleset.

The game may start only after both PlayerAgents explicitly agree on:

- the same published ruleset name;
- the same published ruleset SHA256 hash;
- team names;
- role schedule;
- randomness protocol;
- timeout/retry policy;
- integrity promise.

After the first sub-game starts, the rules are frozen and may not be renegotiated.

### 5.1 Protocol state machine

```text
DISCOVER_OPPONENT
-> EXCHANGE_CAPABILITIES
-> PROPOSE_RULESET
-> ACCEPT_RULESET_HASH
-> DETERMINE_TEAM_ORDER
-> CONFIRM_ROLE_SCHEDULE
-> CONFIRM_TIMEOUT_AND_RETRY_POLICY
-> COMMIT_RANDOM_NONCES
-> REVEAL_RANDOM_NONCES
-> CONFIRM_INTEGRITY_PROMISE
-> START_SUB_GAME
-> PLAY_TURNS
-> CONFIRM_SUB_GAME_RESULT
-> NEXT_SUB_GAME or FINAL_REPORT
-> CONFIRM_FINAL_REPORT
-> SEND_EMAIL_REPORT
-> DONE
```

### 5.2 Capability exchange

Each PlayerAgent must send or make available:

- team name;
- student names/IDs if required by the course;
- MCP endpoint URL(s);
- GitHub repository URL;
- supported ruleset name;
- supported ruleset SHA256 hash;
- confirmation that it is role-flexible and can play both Cop and Robber;
- supported timeout/retry policy;
- supported action vocabulary;
- whether it supports automatic JSON email report sending.

### 5.3 Ruleset hash hard requirement

Either both PlayerAgents accept the exact same published ruleset name and SHA256 hash, or the game does not start.

Canonical acceptance message:

```text
I accept ruleset <ruleset_name> with hash <ruleset_hash>.
```

If the two PlayerAgents do not accept the exact same ruleset name and hash, terminate with protocol failure.

Protocol failure before the first sub-game is not a win or loss for either player.

### 5.4 Fixed official rules

The following rules are fixed for the official assignment-compatible game and may not be changed during pre-game negotiation:

```text
grid_size = 5x5
wrap_around = false
movement = one adjacent cell per move
diagonal_movement = allowed
diagonal_corner_cutting = allowed
passing = forbidden
robber_moves_first = true
max_rounds = 25 full rounds
num_valid_sub_games = 6
role_balance = each participant plays 3 sub-games as Cop and 3 as Robber
cop_block_budget = exactly 5 blocks per sub-game
block_placement = Cop current cell only
block_duration = permanent until sub-game end
blocks_reset_each_sub_game = true
scoring.cop_win = Cop 20, Robber 5
scoring.robber_win = Cop 5, Robber 10
invalid_or_unclear_action_retries = 1
timeout_retries = 1
illegal_action_causes_immediate_loss = true
```

In particular, the Cop block budget is fixed at exactly **5 blocks per sub-game** for the official ruleset.

A lower block budget is not allowed.

A higher block budget creates a different game variant and therefore requires a different ruleset name and hash.

### 5.5 Allowed pre-game confirmations

The PlayerAgents may confirm game-instance parameters that do not change the core game rules.

Allowed confirmations include:

```text
team names
player identifiers
public endpoint URLs
ruleset name and hash
timeout duration in seconds
randomness protocol
role schedule derived from team-name ordering
sub-game start procedure
log format
final report confirmation process
```

These parameters must be agreed before sub-game 1 starts.

### 5.6 Team-name ordering and role schedule

The order of roles is determined by normalized team names.

Normalization procedure:

```text
1. Trim leading and trailing whitespace.
2. Convert to lowercase.
3. Compare lexicographically.
```

The lexicographically smaller team name is **Team A**.

The lexicographically larger team name is **Team B**.

Role schedule:

| Sub-games | Team A role | Team B role |
|---|---|---|
| 1-3 | Cop | Robber |
| 4-6 | Robber | Cop |

Because the Robber always moves first inside each sub-game:

```text
Sub-games 1-3: Team B performs the first action.
Sub-games 4-6: Team A performs the first action.
```

If the normalized team names are identical, the PlayerAgents must use distinct display names before the game starts.

The role schedule must be confirmed before sub-game 1 starts.

### 5.7 Random initial-position agreement

Initial positions must be generated fairly.

For local testing, a fixed shared seed may be used.

For inter-student games, the PlayerAgents must use a commit-reveal protocol.

Commit-reveal protocol:

```text
1. PlayerAgent A generates nonce_A and sends hash(nonce_A).
2. PlayerAgent B generates nonce_B and sends hash(nonce_B).
3. PlayerAgent A reveals nonce_A.
4. PlayerAgent B reveals nonce_B.
5. Both PlayerAgents verify the revealed nonces against the earlier hashes.
6. For each sub-game i, both compute:

   seed_i = SHA256(nonce_A || nonce_B || i)

7. Starting positions are generated deterministically from seed_i.
8. If both generated cells are identical, deterministic generation continues until two disjoint legal cells are produced.
```

Both PlayerAgents must log:

```text
hash(nonce_A)
hash(nonce_B)
nonce_A
nonce_B
derived seed for each sub-game
initial Cop position for each sub-game
initial Robber position for each sub-game
```

### 5.8 Timeout and retry agreement

Before the game starts, both PlayerAgents must agree on the same timeout duration.

The timeout duration must be the same for both PlayerAgents.

Required retry policy:

```text
invalid_or_unclear_action_retries = 1
timeout_retries = 1
```

If an action message is invalid or unclear:

```text
1. The acting player receives one retry.
2. If the retry is still invalid or unclear, the acting player loses.
```

If an action message times out or is missing:

```text
1. The acting player receives one retry.
2. If the retry also times out or is missing, the acting player loses.
```

Illegal actions are different from unclear actions.

A clear but illegal action causes immediate loss for the acting player and does not receive a retry.

### 5.9 Integrity promise

Before the first sub-game starts, both PlayerAgents must explicitly promise to follow the rules.

Canonical integrity promise:

```text
I agree to follow the accepted ruleset.
I will not cheat, lie, or intentionally misrepresent actions, positions, blocks, logs, legal moves, terminal conditions, scores, or reports.
I will maintain my own inferred board state from the initial positions and public action history.
I will admit loss if I have no legal action.
```

If either PlayerAgent refuses to make this promise, the game must not start.

The refusal is recorded as:

```text
pre_game_protocol_failure
```

It is not a win or loss for either player.

### 5.10 Sub-game initialization

For each sub-game, both PlayerAgents confirm:

- sub-game index;
- ruleset name and hash;
- role assignment;
- seed derivation data;
- initial Cop coordinate;
- initial Robber coordinate;
- Robber moves first.

Example:

```text
Starting sub-game 1.
Ruleset: cop-robber-grid-v1.
Ruleset hash: sha256:...
Role schedule: Team A = Cop, Team B = Robber.
Initial positions: C=e4, R=b2.
Robber moves first.
```

### 5.11 Turn acknowledgement

After receiving an action, the opponent should acknowledge successful parsing.

Example:

```text
Acknowledged. I parsed your action as: up-right diagonal.
My inferred state is updated.
```

If unclear:

```text
Your action message is unclear. Please retry once using one canonical action:
up, up-right diagonal, right, right-down diagonal, down, down-left diagonal, left, left-up diagonal, I place a block, or I've lost the game.
```

### 5.12 End-of-sub-game confirmation

At terminal condition, agents exchange:

- winner;
- terminal reason;
- final position/state;
- tournament-style log;
- structured log hash;
- sub-game score.

Both agents must confirm matching result data.

If logs disagree, the public message history is used to identify the mismatch. If unresolved, the sub-game is invalid/failed.

### 5.13 Final report confirmation

After 6 valid sub-games, both agents exchange final JSON report hashes.

If hashes match:

- set `mutual_agreement` to `true`;
- both teams send the JSON report email independently.

If hashes do not match:

- do not claim successful agreement;
- mark the inter-group report as failed or `mutual_agreement: false`;
- the bonus may be invalid.

### 5.14 Negotiation failure

The game must not start if the PlayerAgents fail to agree on any required pre-game item, including:

```text
ruleset name
ruleset hash
team-name ordering
role schedule
timeout duration
randomness protocol
initial-position generation
integrity promise
```

Such a failure is recorded as:

```text
pre_game_protocol_failure
```

It is not counted as a valid sub-game.

It is not scored as a win or loss.

### 5.15 Rule freezing

After both PlayerAgents accept the ruleset and the first sub-game begins, the rules are frozen.

No rule may be renegotiated during:

```text
a sub-game
the full 6-sub-game match
a terminal-condition dispute
score calculation
final report confirmation
```

If a disagreement occurs after the game starts, it must be resolved using:

```text
1. the accepted ruleset name and hash;
2. the public message history;
3. both players' logs;
4. the agreed terminal-condition rules;
5. the agreed scoring rules.
```

A player may not use post-start disagreement as a reason to alter the rules.

### 5.16 Pre-game agreement summary format

Each PlayerAgent should record the completed pre-game agreement in the game log.

Recommended summary format:

```yaml
pre_game_agreement:
  ruleset_name: <ruleset_name>
  ruleset_hash: <ruleset_hash>
  team_a: <team_a_name>
  team_b: <team_b_name>
  role_schedule:
    sub_games_1_to_3:
      team_a: Cop
      team_b: Robber
    sub_games_4_to_6:
      team_a: Robber
      team_b: Cop
  max_rounds: 25
  num_valid_sub_games: 6
  cop_block_budget: 5
  timeout_seconds: <timeout_seconds>
  invalid_action_retries: 1
  timeout_retries: 1
  randomness_protocol: commit_reveal
  integrity_promise_confirmed: true
```


---

## 6. Board Rules

### 6.1 Grid size

The default board is a rectangular **5x5** grid.

The implementation must support configurable grid size through a central configuration file.

Do not hard-code game parameters.

Recommended field:

```json
{
  "grid_size": [5, 5]
}
```

### 6.2 No wrap-around

The grid has fixed boundaries.

There is **no wrap-around**:

- moving left from the leftmost column is illegal;
- moving right from the rightmost column is illegal;
- moving down from the bottom row is illegal;
- moving up from the top row is illegal.

The board is not toroidal.

### 6.3 Coordinate system

Use chess-like coordinates:

- horizontal axis: `a, b, c, d, e, ...`;
- vertical axis: `1, 2, 3, 4, 5, ...`.

For the default 5x5 grid, valid coordinates are:

```text
a5 b5 c5 d5 e5
a4 b4 c4 d4 e4
a3 b3 c3 d3 e3
a2 b2 c2 d2 e2
a1 b1 c1 d1 e1
```

Direction mapping:

| Direction | Coordinate effect |
|---|---|
| `up` | rank `+1` |
| `down` | rank `-1` |
| `right` | file `+1` |
| `left` | file `-1` |
| `up-right diagonal` | file `+1`, rank `+1` |
| `right-down diagonal` | file `+1`, rank `-1` |
| `down-left diagonal` | file `-1`, rank `-1` |
| `left-up diagonal` | file `-1`, rank `+1` |

---

## 7. Initial Positions and Randomness

### 7.1 Initial positions

At the beginning of each sub-game:

- the Cop starts on a randomly selected cell;
- the Robber starts on a randomly selected cell;
- the two starting cells must be disjoint;
- the Cop and Robber cannot start on the same cell;
- both initial positions are known to both agents.

### 7.2 Local testing seed

For local testing, a fixed seed from config is allowed.

### 7.3 Inter-student fair seed generation

For inter-student/inter-group games, use a deterministic commit-reveal protocol to avoid seed manipulation.

Protocol per sub-game:

1. Agent A creates random secret `nonce_A`.
2. Agent B creates random secret `nonce_B`.
3. Agent A sends `hash(nonce_A)`.
4. Agent B sends `hash(nonce_B)`.
5. Agent A reveals `nonce_A`.
6. Agent B reveals `nonce_B`.
7. Both compute:

```text
seed_i = SHA256(nonce_A || nonce_B || sub_game_index || ruleset_hash)
```

8. Both independently generate disjoint Cop/Robber starting cells from `seed_i` using the same deterministic algorithm.

The seed, nonce hashes, revealed nonces, and generated positions must be logged.

### 7.4 Deterministic initial-position generation

Use a deterministic mapping from seed to two disjoint cells.

Example acceptable method:

1. List all grid cells in coordinate order: `a1, b1, c1, ..., a2, b2, ...`.
2. Use a seeded pseudorandom generator initialized with `seed_i`.
3. Sample Cop cell.
4. Sample Robber cell from remaining cells.
5. Verify disjointness.

Both agents must implement the same algorithm.

---

## 8. Turn Order and Move Limit

### 8.1 Turn order

The Robber moves first.

Then the Cop acts.

One full round is:

```text
Robber action -> Cop action
```

The order repeats:

```text
Round 1: Robber -> Cop
Round 2: Robber -> Cop
...
Round 25: Robber -> Cop
```

### 8.2 Meaning of 25 moves

For this implementation, `25 moves` means **25 full rounds**.

Therefore, each valid sub-game allows at most:

- 25 Robber actions;
- 25 Cop actions.

If the Cop completes the action of round 25 and no terminal condition has occurred, the Robber wins.

---

## 9. Movement Rules

### 9.1 One adjacent cell per movement action

Each movement action moves the acting player to exactly one adjacent cell.

Movement can be:

- horizontal;
- vertical;
- diagonal.

### 9.2 Legal movement directions

The following directions are legal if the target cell is inside the board and not blocked:

```text
up
up-right diagonal
right
right-down diagonal
down
down-left diagonal
left
left-up diagonal
```

### 9.3 Diagonal movement and corner-cutting

Diagonal movement is allowed.

Diagonal corner-cutting is allowed.

A diagonal move is legal if:

1. the diagonal target cell is inside the board;
2. the diagonal target cell is not blocked.

The two orthogonally adjacent side cells do not matter.

Example: from `c3` to `d4` is legal if `d4` is free, even if `c4` or `d3` is blocked.

### 9.4 No passing

Neither player may pass.

- The Robber must move on every Robber turn.
- The Cop must either move or place a block on every Cop turn.

---

## 10. Cop Blocks / Barriers

### 10.1 Who may place blocks

Only the Cop may place blocks.

The Robber cannot place blocks.

### 10.2 Maximum number of blocks

The Cop may place at most **5** blocks per sub-game.

Recommended field:

```json
{
  "max_barriers": 5
}
```

### 10.3 Block placement replaces movement

On the Cop's turn, the Cop must choose exactly one action type:

1. move to one adjacent cell; or
2. place a block on the Cop's current cell.

The Cop cannot both move and place a block on the same turn.

### 10.4 Block location

A block can only be placed on the cell where the Cop is currently standing.

The Cop cannot place a block:

- on the Robber's current cell;
- on an arbitrary cell elsewhere on the board;
- on an already blocked cell.

### 10.5 Cop standing on a newly blocked cell

When the Cop places a block, the block is placed on the Cop's current cell.

The Cop is temporarily allowed to stand on that newly blocked cell until the Cop's next turn.

On the Cop's next turn:

- the Cop must move away from that blocked cell;
- the Cop cannot place another block while standing on a blocked cell.

If the Cop cannot move away from the blocked cell on the next Cop turn, the Cop loses because he has no legal action.

### 10.6 Block effect

A blocked cell is impassable to both players.

No player may enter a blocked cell.

A blocked cell acts like a wall or board boundary.

### 10.7 Block duration

Blocks are permanent until the end of the current sub-game.

Blocks reset between sub-games.

At the start of every new sub-game:

- there are no blocks on the board;
- the Cop's used block count is reset to `0`.

---

## 11. Capture, Loss, and Terminal Conditions

### 11.1 Cop capture

The Cop wins immediately if the Cop moves into the Robber's current cell.

Terminal reason: `cop_capture`.

### 11.2 Robber moves into the Cop

If the Robber moves into the Cop's current cell, the Robber loses immediately.

This is treated as a Cop win.

Terminal reason: `robber_moved_into_cop`.

### 11.3 Robber has no legal move

If the Robber has no legal move on the Robber's turn, the Robber loses.

This is treated as a Cop win.

Terminal reason: `robber_no_legal_move`.

### 11.4 Cop has no legal action

If the Cop has no legal action on the Cop's turn, the Cop loses.

A legal Cop action is either:

1. a legal movement action; or
2. a legal block placement action.

A block placement is legal only if:

- the Cop has not already placed the maximum number of blocks;
- the Cop is not currently standing on an already blocked cell;
- the Cop's current cell is not already blocked.

Terminal reason: `cop_no_legal_action`.

### 11.5 Round-limit Robber win

If round 25 is completed without any capture, forced loss, illegal action, invalid action, timeout, or other terminal condition, the Robber wins.

The Robber's survival condition is checked after the Cop's action in round 25.

Terminal reason: `round_limit_reached`.

### 11.6 Illegal actions

An illegal action causes immediate loss for the acting player.

Illegal movement includes moving:

- outside the board;
- into a blocked cell;
- more than one cell away;
- in a non-supported direction;
- from an incorrect inferred current position.

Illegal block placement includes:

- Robber attempting to place a block;
- Cop placing more than 5 blocks in a sub-game;
- Cop placing a block while standing on an already blocked cell;
- Cop placing a block anywhere other than his current cell;
- Cop combining movement and block placement in one turn.

Terminal reasons:

- `robber_illegal_action`;
- `cop_illegal_action`.

### 11.7 Invalid/unclear action messages

If an agent produces an invalid, unclear, malformed, or unparseable action message:

1. the receiving agent asks for one retry;
2. if the retry is still invalid or unclear, the acting agent loses.

Terminal reasons:

- `robber_invalid_action_retry_failed`;
- `cop_invalid_action_retry_failed`.

### 11.8 Timeout / no response

If an agent times out or does not respond:

1. the opponent asks for one retry;
2. if the retry also times out or does not produce a valid action, the acting agent loses.

Terminal reasons:

- `robber_timeout_retry_failed`;
- `cop_timeout_retry_failed`.

Timeout duration must be configurable and equal for both players.

---

## 12. Communication Rules

### 12.1 Natural language

Agents must communicate in natural language, in English.

### 12.2 Required action meanings

Each action message must honestly describe exactly one action.

Canonical movement action meanings:

```text
I move up.
I move up-right diagonal.
I move right.
I move right-down diagonal.
I move down.
I move down-left diagonal.
I move left.
I move left-up diagonal.
```

Canonical Cop block action:

```text
I place a block.
```

Canonical forced-loss admission:

```text
I've lost the game.
```

Free-form wording is allowed only if it can be unambiguously mapped to one of the canonical meanings.

### 12.3 Coordinates in messages

Coordinates may be included for clarity but are non-authoritative.

Example:

```text
I move down-left diagonal to d2.
```

The authoritative action is the declared direction/action, not the claimed coordinate.

If an agent says:

```text
I move up to c4.
```

but moving `up` from the inferred current cell leads to `c3`, then:

- the declared direction `up` is authoritative;
- the claimed coordinate `c4` is ignored for state-update purposes;
- the contradiction should be logged for debugging.

If the declared direction itself is illegal, the action is illegal.

### 12.4 No cheating or lying

Agents must follow the rules strictly.

Agents are not allowed to:

- lie about their action;
- intentionally misrepresent the board state;
- pretend an illegal action is legal;
- hide a loss condition;
- claim a different move than the one they actually choose;
- manipulate logs or scores.

Before the game begins, the agents must explicitly discuss:

1. the full rule set;
2. their agreement to follow it;
3. their promise not to cheat;
4. their promise not to lie.

### 12.5 Natural-language-only state exchange

Agents do not receive direct coordinate updates after each move.

Agents receive:

- the initial positions;
- the opponent's natural-language action messages;
- their own action history.

Each agent must maintain its own inferred board state from the full public message history.

Because actions are public and honest, the board state should be exactly reconstructible from initial positions and action sequence.

---

## 13. State Knowledge and Partial Observation Interpretation

The lecturer's assignment frames the system as a partially observable multi-agent setting with natural-language communication.

This project uses the following practical interpretation:

- both agents know the initial positions;
- agents do not receive direct state API updates after moves;
- agents receive only natural-language opponent actions;
- agents must infer and maintain the board state themselves;
- no central engine/referee is the source of state truth;
- the agreed rules and public move history are the shared basis for validation.

This is not hidden-state in the strong sense because the full state is reconstructible. It still preserves the assignment's natural-language communication constraint because agents communicate and update state through language rather than direct structured coordinate state updates.

---

## 14. Game Log

### 14.1 Logging requirement

Both agents must maintain a tournament-style game log, similar to chess notation.

The log must contain:

- initial Cop position;
- initial Robber position;
- every Robber action result;
- every Cop action result;
- every block placement;
- winner;
- terminal reason;
- scoring;
- seed information;
- ruleset hash;
- role schedule.

### 14.2 Notation

Symbols:

| Symbol | Meaning |
|---|---|
| `R` | Robber / Thief |
| `C` | Cop |
| `#` | Block placed on the Cop's current cell |
| `move 0` | Initial position |
| `winner: R` | Robber wins |
| `winner: C` | Cop wins |

Examples:

```text
move 0: Re2
move 0: Ce4

move 1: Rd1
move 1: Ce4#

move 2: Rc2
move 2: Cd5

move 3: Rb3
move 3: Cc4

winner: C
terminal_reason: cop_capture
```

`Ce4#` means the Cop is on `e4` and places a block on `e4`.

### 14.3 Structured action log

Each action should also be recorded in structured form.

Movement example:

```json
{
  "round": 1,
  "actor": "R",
  "message": "I move down-left diagonal to d1.",
  "declared_action": "down-left diagonal",
  "claimed_coordinate": "d1",
  "inferred_start": "e2",
  "inferred_end": "d1",
  "valid": true,
  "terminal": false
}
```

Cop block example:

```json
{
  "round": 1,
  "actor": "C",
  "message": "I place a block on e4.",
  "declared_action": "place_block",
  "claimed_coordinate": "e4",
  "inferred_start": "e4",
  "inferred_end": "e4",
  "block_placed": "e4",
  "valid": true,
  "terminal": false
}
```

---

## 15. Scoring

Each sub-game is scored independently.

| Sub-game result | Cop score | Robber score |
|---|---:|---:|
| Cop wins | 20 | 5 |
| Robber wins | 5 | 10 |

### 15.1 Cop win scoring

The Cop receives 20 points and the Robber receives 5 points when the Cop wins by:

- capturing the Robber;
- Robber moving into Cop's cell;
- Robber having no legal move;
- Robber making an illegal move;
- Robber failing an invalid-action retry;
- Robber timing out twice.

### 15.2 Robber win scoring

The Cop receives 5 points and the Robber receives 10 points when the Robber wins by:

- surviving through round 25;
- Cop having no legal action;
- Cop making an illegal move;
- Cop making an illegal block placement;
- Cop failing an invalid-action retry;
- Cop timing out twice.

### 15.3 Full-game scoring

A full game contains 6 valid sub-games.

The maximum possible team score is 90 if the team wins all 3 sub-games as Cop and all 3 sub-games as Robber:

```text
3 * 20 + 3 * 10 = 90
```

The minimum possible team score is 30:

```text
3 * 5 + 3 * 5 = 30
```

---

## 16. MCP and Deployment Requirements

### 16.1 MCP servers

The lecturer's document expects two independent MCP servers for the agents, one for Cop and one for Thief/Robber. In this implementation, the code must be role-flexible, but running deployments must still make the required endpoints clear.

Acceptable approaches:

1. run two independent PlayerAgent instances from the same codebase, each assigned its current role per sub-game;
2. expose role-specific MCP routes/tools backed by the same role-flexible PlayerAgent implementation;
3. if using a single endpoint per team, provide the same role-flexible endpoint in both assignment-compatible URL fields and document the design clearly.

For maximum compatibility with the lecturer's JSON examples and other students, prefer exposing explicit Cop and Robber URL fields even if both are backed by the same codebase.

### 16.2 Local first, then cloud

Implementation should support:

1. local execution on `localhost`, with two agents running on separate ports;
2. cloud/public deployment after local validation.

Local example:

```text
localhost:8001 -> PlayerAgent instance A
localhost:8002 -> PlayerAgent instance B
```

### 16.3 Security and authentication

Public MCP endpoints must use authentication.

Requirements:

- use token-based authentication;
- support token revocation;
- do not expose unauthenticated public endpoints;
- do not commit tokens, API keys, OAuth secrets, or credentials;
- ensure public MCP URLs are reachable from the internet and not blocked by firewalls;
- document how to configure tokens locally and in deployment.

### 16.4 LLM connection options

The lecturer's document discusses several LLM architectures. Any is acceptable if documented and secure:

1. public cloud LLM API such as OpenAI, Anthropic, Gemini;
2. local Ollama exposed securely through a tunnel/proxy;
3. hybrid approach where local client calls local LLM and cloud MCP servers only expose tools.

Recommended for simplicity: use a public LLM API from the agent client code.

If using local Ollama, do not expose the raw Ollama port directly without authentication.

### 16.5 FastMCP

FastMCP is an acceptable implementation framework for exposing MCP tools.

---

## 17. Configuration Requirements

All game parameters must be centralized in `config.json` or `config.yaml`.

Hard-coding game parameters is forbidden.

Required or recommended configuration fields:

```json
{
  "ruleset_name": "cop-robber-grid-v1",
  "ruleset_hash": "sha256:<computed-from-published-ruleset>",
  "grid_size": [5, 5],
  "max_rounds": 25,
  "num_sub_games": 6,
  "max_barriers": 5,
  "turn_order": ["robber", "cop"],
  "movement": {
    "allow_diagonal": true,
    "allow_corner_cutting": true,
    "allow_pass": false,
    "wrap_around": false,
    "step_size": 1
  },
  "initial_position_policy": "commit_reveal_random_disjoint",
  "coordinates": {
    "style": "chess_like",
    "files": "letters",
    "ranks": "positive_integers",
    "up_means_rank_plus_one": true
  },
  "barriers": {
    "enabled": true,
    "placer": "cop_only",
    "placement_location": "cop_current_cell",
    "placement_replaces_movement": true,
    "permanent_until_sub_game_end": true,
    "reset_each_sub_game": true
  },
  "validation": {
    "invalid_action_retries": 1,
    "timeout_retries": 1,
    "illegal_action_causes_loss": true,
    "coordinates_in_messages_are_authoritative": false,
    "central_engine_enabled": false
  },
  "timeouts": {
    "action_timeout_seconds": 60
  },
  "scoring": {
    "cop_win": {
      "cop": 20,
      "robber": 5
    },
    "robber_win": {
      "cop": 5,
      "robber": 10
    }
  },
  "email_report": {
    "enabled": true,
    "recipient": "rmisegal+uoh26b@gmail.com",
    "body_format": "json_only"
  }
}
```

---

## 18. JSON Reports and Automatic Email Requirement

### 18.1 Email recipient

After the games are completed, the final result report must be sent by email to:

```text
rmisegal+uoh26b@gmail.com
```

### 18.2 Who sends the email

For an internal same-team game:

- the team's agent/system sends the final JSON report email.

For an inter-student / inter-group game:

- both teams must independently send an email;
- both emails must describe the same agreed result;
- both reports must match semantically;
- `mutual_agreement` must be `true` for a valid agreed inter-group report.

### 18.3 Sending mechanism

The report should be sent automatically by the agent/system, not manually by a human.

Recommended implementation:

```python
def send_final_report_email(report_json: dict) -> None:
    ...
```

Use Gmail API / Google API Client with OAuth/token-based authentication.

Do not use hard-coded email username/password.

Do not commit credentials or OAuth tokens to GitHub.

### 18.4 Email body must be JSON only

The email body must contain only valid JSON.

Do not include prose, markdown, greeting text, explanations, or signatures.

Wrong:

```text
Hello professor,
Here are our results...
```

Correct:

```json
{
  "report_type": "bonus_game",
  "groups": {
    "group_1": "Team-Alpha",
    "group_2": "Team-Beta"
  },
  "sub_games": [],
  "totals_by_group": {
    "Team-Alpha": 60,
    "Team-Beta": 80
  },
  "mutual_agreement": true
}
```

### 18.5 Internal game JSON report

For an internal team game, use at least this structure:

```json
{
  "group_name": "Team-Alpha",
  "students": [],
  "github_repo": "https://github.com/team-alpha/marl-cop-thief",
  "cop_mcp_url": "https://cop-mcp-alpha.example.com",
  "thief_mcp_url": "https://thief-mcp-alpha.example.com",
  "timezone": "Asia/Jerusalem",
  "ruleset_name": "cop-robber-grid-v1",
  "ruleset_hash": "sha256:...",
  "sub_games": [],
  "totals": {
    "cop": 90,
    "thief": 40
  }
}
```

### 18.6 Inter-group bonus JSON report

For an inter-group bonus game, use at least this structure:

```json
{
  "report_type": "bonus_game",
  "groups": {
    "group_1": "Team-Alpha",
    "group_2": "Team-Beta"
  },
  "github_repo_group_1": "https://github.com/team-alpha/marl-cop-thief",
  "github_repo_group_2": "https://github.com/team-beta/marl-cop-thief",
  "mcp_url_group_1_cop": "https://cop-mcp-alpha.example.com",
  "mcp_url_group_1_thief": "https://thief-mcp-alpha.example.com",
  "mcp_url_group_2_cop": "https://cop-mcp-beta.example.com",
  "mcp_url_group_2_thief": "https://thief-mcp-beta.example.com",
  "timezone": "Asia/Jerusalem",
  "students_group_1": [],
  "students_group_2": [],
  "ruleset_name": "cop-robber-grid-v1",
  "ruleset_hash": "sha256:...",
  "role_schedule": {},
  "seed_protocol": "commit_reveal",
  "sub_games": [],
  "totals_by_group": {
    "Team-Alpha": 60,
    "Team-Beta": 80
  },
  "bonus_claim": {
    "Team-Alpha": 7,
    "Team-Beta": 10
  },
  "mutual_agreement": true
}
```

### 18.7 Sub-game report fields

Each `sub_games` item should include:

```json
{
  "sub_game_index": 1,
  "team_a_role": "cop",
  "team_b_role": "robber",
  "initial_positions": {
    "cop": "e4",
    "robber": "b2"
  },
  "seed_hashes": {
    "team_a_commitment": "sha256:...",
    "team_b_commitment": "sha256:...",
    "derived_seed": "sha256:..."
  },
  "moves": [],
  "winner_role": "cop",
  "winner_team": "Team-Alpha",
  "terminal_reason": "cop_capture",
  "scores": {
    "cop": 20,
    "robber": 5,
    "Team-Alpha": 20,
    "Team-Beta": 5
  },
  "log_hash": "sha256:..."
}
```

---

## 19. Inter-Group Bonus Rules

The lecturer's document defines an optional inter-group bonus competition.

### 19.1 Eligibility and timing

- Bonus games are beyond the mandatory same-team agent pair.
- The bonus series should be submitted within the required time window from assignment publication.
- A bonus series is between two groups/teams.
- Each pair of teams runs one full inter-group series of 6 valid sub-games.

### 19.2 Role exchange

For inter-group games:

- in the first 3 sub-games, one team plays Cop and the other plays Robber;
- in the remaining 3 sub-games, roles are swapped.

In this implementation, the first-role assignment is determined by lexicographic team ordering as described in Section 5.6.

### 19.3 Bonus scoring

For a valid inter-group series:

- the team with the higher accumulated score receives 10 bonus points;
- the losing team receives 7 bonus points;
- in an exact draw, each team receives 5 bonus points.

If multiple valid bonus series are played against different groups, the final bonus score is the average of the valid series results, according to the lecturer's rules.

### 19.4 Mismatched reports

If the two teams' reports do not match, or if mutual agreement is missing/false, the bonus for that series is invalid and may count as 0 for both sides.

---

## 20. README / Scientific Report Requirements

The GitHub repository must include a detailed `README.md` written at a scientific/engineering level.

The README should include:

### 20.1 Formal model

Describe the pursuit problem as a decentralized partially observable game / Dec-POMDP.

Use the tuple:

```text
<n, S, {A_i}, P, R, {Ω_i}, O, γ>
```

Explain:

- `n`: number of agents;
- `S`: state space, including player positions and barriers;
- `{A_i}`: action spaces for Cop and Robber;
- `P`: transition function;
- `R`: reward/scoring function;
- `{Ω_i}`: partial observation spaces;
- `O`: observation function;
- `γ`: discount factor if learning is used.

Explain the practical partial-observation interpretation used here: no direct state updates after actions; state is reconstructed from natural-language messages.

### 20.2 Orchestration and communication challenges

Discuss:

- MCP client/server design;
- why each PlayerAgent is both MCP server and MCP client;
- no-central-orchestrator correspondence-game design;
- natural-language ambiguity;
- action parsing;
- retry protocol;
- log reconciliation;
- inter-student compatibility;
- security and deployment challenges.

### 20.3 Evidence and artifacts

Include relevant evidence:

- local run logs;
- MCP communication logs;
- game logs;
- JSON reports;
- email report examples or redacted logs;
- screenshots of GUI if implemented;
- plots/learning curves if Q-learning or other learning is used.

### 20.4 Deployment documentation

Document:

- how to run locally;
- how to configure tokens;
- how to start two agents;
- how to run an internal 6-sub-game match;
- how to run an inter-group match;
- how to deploy public MCP endpoints;
- how to send the final email report.

---

## 21. Recommended Sanity Checks and Development Stages

The lecturer recommends gradual sanity checks on smaller grids before final 5x5 evaluation.

Recommended progression:

1. **2x2**: basic algorithmic sanity check, message-passing pipeline verification.
2. **3x3 / 3x2**: coordination convergence, hyperparameter tuning, failure detection.
3. **4x4 / 4x3**: partial-observation ambiguity and initial distance larger than observation radius, if an observation radius is implemented.
4. **5x5**: final full game, graph/report generation, full analysis.

Suggested implementation stages:

1. implement rules and state model;
2. implement movement, barriers, capture, and legal-action detection;
3. implement one role-flexible PlayerAgent locally;
4. run two local PlayerAgent instances;
5. implement natural-language action parser;
6. implement MCP server/client tools;
7. implement ruleset-hash agreement;
8. implement commit-reveal seed generation;
9. implement structured logs and final JSON report;
10. implement email sending;
11. deploy MCP endpoints publicly with authentication;
12. run inter-group game.

---

## 22. Optional Strategy / Learning Component

The lecturer discusses Q-learning as an optional recommended approach, not a mandatory requirement.

Allowed strategies include:

- heuristic distance-based policies;
- minimax/game-search on the local inferred state;
- rule-based policies;
- LLM-prompted reasoning;
- tabular Q-learning;
- hybrid approaches.

If Q-learning is implemented, document:

- state representation;
- action representation;
- reward design;
- training episodes;
- learning curves;
- final policy behavior.

No deep reinforcement learning is required.

---

## 23. GUI Requirement Status

The lecturer lists GUI development as a recommended engineering stage for visualizing agent movement and barriers.

For this implementation:

- GUI is recommended but not treated as a core protocol requirement;
- if implemented, it should display the grid, both agents, blocks, turn number, and terminal result;
- if not implemented, provide textual/JSON logs sufficient to reconstruct the game.

If time permits, include screenshots in the README.

---

## 24. Security Requirements

### 24.1 Secrets

Never commit:

- LLM API keys;
- Gmail OAuth tokens;
- MCP authentication tokens;
- ngrok/Localtonet credentials;
- service-account credentials;
- private URLs intended to be secret.

Use `.env`, local secret storage, or deployment secret managers.

### 24.2 Public endpoints

Public MCP endpoints must:

- use HTTPS where possible;
- require token authentication;
- support token revocation;
- avoid exposing raw local LLM endpoints;
- avoid exposing raw Ollama ports;
- be tested from outside the local machine/network.

### 24.3 Email credentials

Use Gmail API / Google OAuth.

Do not use raw passwords or app passwords unless explicitly approved and securely stored.

---

## 25. Terminal Reason Codes

Use these terminal reason codes in logs and reports:

| Code | Winner | Meaning |
|---|---|---|
| `cop_capture` | Cop | Cop moved into Robber's cell |
| `robber_moved_into_cop` | Cop | Robber moved into Cop's cell |
| `robber_no_legal_move` | Cop | Robber had no legal move |
| `cop_no_legal_action` | Robber | Cop had no legal move or legal block action |
| `robber_illegal_action` | Cop | Robber made an illegal action |
| `cop_illegal_action` | Robber | Cop made an illegal action |
| `robber_invalid_action_retry_failed` | Cop | Robber failed retry after invalid/unclear message |
| `cop_invalid_action_retry_failed` | Robber | Cop failed retry after invalid/unclear message |
| `robber_timeout_retry_failed` | Cop | Robber timed out twice |
| `cop_timeout_retry_failed` | Robber | Cop timed out twice |
| `round_limit_reached` | Robber | 25 full rounds completed without Cop win |
| `technical_failure_rerun` | None | Sub-game canceled and rerun due to real technical failure |
| `protocol_failure` | None | Game did not start or cannot continue due to protocol mismatch |

---

## 26. Required MCP Tool Surface

Exact function names may differ, but each PlayerAgent should expose MCP tools equivalent to the following.

### 26.1 Pre-game tools

```text
get_capabilities()
propose_ruleset(ruleset_name, ruleset_hash)
accept_ruleset(ruleset_name, ruleset_hash)
exchange_team_identity(team_name, students, repo_url, mcp_urls)
commit_nonce(sub_game_index, nonce_hash)
reveal_nonce(sub_game_index, nonce)
confirm_role_schedule(schedule)
confirm_integrity_promise(message)
```

### 26.2 Game tools

```text
start_sub_game(sub_game_index, role, initial_positions, seed_data)
receive_action_message(sub_game_index, round_index, actor, message)
request_action_retry(sub_game_index, round_index, reason)
confirm_action_parse(sub_game_index, round_index, parsed_action)
confirm_sub_game_result(sub_game_index, result_hash, result_json)
```

### 26.3 Reporting tools

```text
get_sub_game_log(sub_game_index)
get_final_report()
confirm_final_report(report_hash)
send_final_report_email(report_json)
```

All externally callable tools must validate authentication.

---

## 27. Completion Checklist

The implementation is complete when all of the following are true:

### Core game

- [ ] PlayerAgent can play both Cop and Robber.
- [ ] Grid is configurable, default 5x5.
- [ ] No wrap-around movement.
- [ ] Chess-like coordinate system implemented.
- [ ] One-step 8-direction movement implemented.
- [ ] Diagonal corner-cutting allowed.
- [ ] Passing forbidden.
- [ ] Cop block rules implemented.
- [ ] Terminal conditions implemented.
- [ ] 25 full rounds implemented.
- [ ] 6 valid sub-games implemented.
- [ ] Scoring implemented.

### Correspondence protocol

- [ ] No central referee/engine controls state.
- [ ] Each agent maintains inferred state independently.
- [ ] Natural-language action messages are used.
- [ ] Canonical action parser implemented.
- [ ] Coordinates in messages are non-authoritative.
- [ ] Invalid-action retry implemented.
- [ ] Timeout retry implemented.
- [ ] Illegal action immediate loss implemented.
- [ ] Logs are maintained by both agents.

### Inter-group compatibility

- [ ] Ruleset hash agreement implemented.
- [ ] Game does not start on ruleset mismatch.
- [ ] Deterministic role ordering by team name implemented.
- [ ] Commit-reveal seed protocol implemented.
- [ ] Sub-game result confirmation implemented.
- [ ] Final report hash confirmation implemented.

### MCP/deployment

- [ ] PlayerAgent exposes MCP tools.
- [ ] PlayerAgent can call opponent MCP tools.
- [ ] Local two-agent run works.
- [ ] Public/cloud endpoint is supported or documented.
- [ ] Token authentication implemented for public endpoints.

### Reporting

- [ ] Internal game JSON report generated.
- [ ] Inter-group bonus JSON report generated.
- [ ] Email body is JSON only.
- [ ] Gmail API/OAuth sending implemented or clearly documented.
- [ ] Both teams independently send matching reports for inter-group games.

### Repository/report

- [ ] `config.json` or `config.yaml` contains game parameters.
- [ ] No hard-coded game parameters.
- [ ] README includes formal Dec-POMDP model.
- [ ] README explains architecture and no-orchestrator correspondence design.
- [ ] README includes local/cloud run instructions.
- [ ] README includes logs, report examples, screenshots/plots if available.
- [ ] Secrets are not committed.

---

## 28. Items from Lecturer's Document That Are Easy to Miss

The following requirements/recommendations from the lecturer's assignment must not be forgotten:

1. **Two autonomous agents communicating through MCP** are the core of the assignment.
2. **Natural-language communication** is required; agents should not rely on direct rigid numeric location passing after initialization.
3. The assignment frames the problem as **partially observable / Dec-POMDP**, so the README must address that formally.
4. The game defaults are **5x5**, **25 moves**, **6 sub-games**, **5 barriers**, and the given scoring table.
5. **Diagonal movement is explicitly allowed** in the lecturer's game description.
6. **Cop barriers are an alternative to movement** and are placed on the Cop's current square.
7. **Hard-coding game parameters is forbidden**; use config.
8. **Automatic email reporting is required**; the email body must contain only structured JSON.
9. The target email is `rmisegal+uoh26b@gmail.com`.
10. **Gmail API / Google API Client** is recommended for reliable and secure reporting.
11. Games that fail because of **technical failure** should be rerun until 6 valid sub-games are completed.
12. The internal report and inter-group report must contain the required GitHub/MCP URL/team/student/result fields.
13. For inter-group bonus, **both teams must send matching reports**; mismatched reports can invalidate the bonus.
14. Cloud deployment requires attention to **public reachability, authentication tokens, revocation, and firewall issues**.
15. Q-learning is discussed as useful/recommended but is **optional**, not mandatory.
16. The README scientific report must include formal modeling, orchestration/communication analysis, and evidence such as logs/graphs/screenshots when applicable.
17. Gradual sanity checks on smaller grids are recommended before final 5x5 runs.
18. The final emphasis is system engineering, agent orchestration, communication, and robust autonomous pipeline, not only winning strategy.

---

## 29. Final One-Page Rule Summary

```text
Agents: two independent role-flexible PlayerAgents
Roles: Cop and Robber/Thief; assigned per sub-game
Architecture: no central strategic orchestrator/referee; correspondence game via MCP
Communication: English natural-language action messages
State: initial positions known; later state inferred from public messages
Grid: configurable rectangular grid, default 5x5
Wrap-around: no
Coordinates: chess-like, e.g. a1-e5
Initial positions: random disjoint cells via commit-reveal seed for inter-group games
Turn order: Robber first, then Cop
Move limit: 25 full rounds = 25 Robber actions + 25 Cop actions
Movement: exactly one adjacent cell, including diagonals
Corner-cutting: allowed if target cell is free
Passing: forbidden
Robber action: must move
Cop action: must move or place block
Blocks: Cop only, max 5, only on Cop's current cell
Block duration: permanent until sub-game end
Block reset: yes, every sub-game
Capture: Cop moves into Robber's cell
Robber loses if: moves into Cop, no legal move, illegal/invalid action, timeout failure
Cop loses if: no legal action, illegal/invalid action, timeout failure
Round-limit winner: Robber
Scoring: Cop win = Cop 20 / Robber 5; Robber win = Cop 5 / Robber 10
Full game: 6 valid sub-games
Ruleset agreement: exact same ruleset hash required or game does not start
Role schedule: deterministic by normalized lexicographic team name
Logging: both agents keep tournament-style and structured logs
Reports: final JSON report, JSON-only email body to lecturer
Email recipient: rmisegal+uoh26b@gmail.com
Config: all parameters in config.json/config.yaml; no hard-coding
Security: token-authenticated public MCP endpoints; no committed secrets
```
