# Cop and Robber Grid Game Rules

## 1. Scope and Status

This document is the source of truth for the **game rules** of the Cop and Robber grid game.

It intentionally describes only the game itself:

- board;
- coordinates;
- roles;
- turn order;
- legal actions;
- blocks/barriers;
- terminal conditions;
- communication rules that affect move legality;
- sub-game and full-game structure;
- scoring;
- game notation/logging.

It does **not** define implementation architecture, MCP details, code structure, email reporting, cloud deployment, API usage, or any other technical implementation mechanism.

The terms **Robber** and **Thief** are synonyms. This document uses **Robber** as the primary term.

Before any full game starts, both players must complete the pre-game agreement phase defined in this document.

---

## 2. Roles

Each sub-game has exactly two players:

- **Cop**, denoted `C`;
- **Robber**, denoted `R`.

The Cop tries to catch the Robber.

The Robber tries to avoid capture until the round limit expires.

Both players must follow the same agreed rule set for the entire full game. Rules may not be changed during a sub-game or during a full game.

---

## 3. Full Game and Sub-games

### 3.1 Sub-game

A **sub-game** is one pursuit round between one Cop and one Robber on one grid.

A sub-game ends when one terminal condition occurs, such as capture, forced loss, illegal action, timeout failure, or reaching the round limit.

### 3.2 Full game

A **full game** consists of exactly **6 valid sub-games**.

Scores are accumulated over all 6 sub-games.

### 3.3 Role balance

Across a full game, each participant must play:

- 3 sub-games as Cop;
- 3 sub-games as Robber.

The deterministic role schedule is defined in the pre-game agreement section.

---

## 4. Pre-game Agreement and Limited Negotiation

Before the first sub-game starts, both players must complete a short pre-game agreement phase.

The purpose of this phase is to confirm that both players will play the same game under the same rules. This phase is **not** a free-form negotiation that may silently change the official ruleset.

The game may start only after both players explicitly agree on:

- the same published ruleset name;
- the same published ruleset hash;
- team names;
- role schedule;
- randomness protocol;
- timeout/retry policy;
- integrity promise.

After the first sub-game starts, the rules are frozen and may not be renegotiated.

### 4.1 Ruleset hash agreement

Both players must accept the exact same published ruleset name and hash.

Canonical acceptance message:

```text
I accept ruleset <ruleset_name> with hash <ruleset_hash>.
```

If the two players do not accept the exact same ruleset name and hash, the game must not start.

This is a hard requirement.

A mismatch is recorded as:

```text
pre_game_protocol_failure
```

It is not a win or loss for either player.

### 4.2 Fixed official rules

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

### 4.3 Allowed pre-game confirmations

The players may confirm game-instance parameters that do not change the core game rules.

Allowed confirmations include:

```text
team names
player identifiers
ruleset name and hash
timeout duration in seconds
randomness protocol
role schedule derived from team-name ordering
sub-game start procedure
game record format
```

These parameters must be agreed before sub-game 1 starts.

### 4.4 Team-name ordering and role schedule

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

If the normalized team names are identical, the players must choose distinct display names before the game starts.

The role schedule must be confirmed before sub-game 1 starts.

### 4.5 Random initial-position agreement

Initial positions must be generated fairly.

For local testing, a fixed shared seed may be used.

For inter-student games, the players must use a commit-reveal protocol.

Commit-reveal protocol:

```text
1. Player A generates nonce_A and sends hash(nonce_A).
2. Player B generates nonce_B and sends hash(nonce_B).
3. Player A reveals nonce_A.
4. Player B reveals nonce_B.
5. Both players verify the revealed nonces against the earlier hashes.
6. For each sub-game i, both compute:

   seed_i = SHA256(nonce_A || nonce_B || sub_game_index || ruleset_hash)

7. Starting positions are generated deterministically from seed_i.
8. If both generated cells are identical, deterministic generation continues until two disjoint legal cells are produced.
```

Both players must log:

```text
hash(nonce_A)
hash(nonce_B)
nonce_A
nonce_B
derived seed for each sub-game
initial Cop position for each sub-game
initial Robber position for each sub-game
```

### 4.6 Timeout and retry agreement

Before the game starts, both players must agree on the same timeout duration.

The timeout duration must be the same for both players.

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

### 4.7 Integrity promise

Before the first sub-game starts, both players must explicitly promise to follow the rules.

Canonical integrity promise:

```text
I agree to follow the accepted ruleset.
I will not cheat, lie, or intentionally misrepresent actions, positions, blocks, logs, legal moves, terminal conditions, or scores.
I will maintain my own inferred board state from the initial positions and public action history.
I will admit loss if I have no legal action.
```

If either player refuses to make this promise, the game must not start.

The refusal is recorded as:

```text
pre_game_protocol_failure
```

It is not a win or loss for either player.

### 4.8 Negotiation failure

The game must not start if the players fail to agree on any required pre-game item, including:

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

### 4.9 Rule freezing

After both players accept the ruleset and the first sub-game begins, the rules are frozen.

No rule may be renegotiated during:

```text
a sub-game
the full 6-sub-game match
a terminal-condition dispute
score calculation
final score confirmation
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

### 4.10 Pre-game agreement summary format

Each player should record the completed pre-game agreement in the game record.

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

## 5. Board

### 5.1 Grid

The game is played on a rectangular grid.

The default board size is:

```text
5 x 5
```

The standard/default board therefore contains 25 cells.

### 5.2 No wrap-around

The board has fixed boundaries.

There is **no wrap-around**:

- moving left from the leftmost column is illegal;
- moving right from the rightmost column is illegal;
- moving down from the bottom row is illegal;
- moving up from the top row is illegal.

The board is not cyclical, not toroidal, and does not connect opposite edges.

### 5.3 Coordinates

Coordinates use chess-like notation:

- horizontal axis: lowercase letters `a, b, c, d, e, ...`;
- vertical axis: positive integers `1, 2, 3, 4, 5, ...`.

For the default 5x5 board, the valid coordinates are:

```text
a5 b5 c5 d5 e5
a4 b4 c4 d4 e4
a3 b3 c3 d3 e3
a2 b2 c2 d2 e2
a1 b1 c1 d1 e1
```

### 5.4 Direction mapping

The direction names have the following coordinate effects:

| Direction | Coordinate effect |
|---|---|
| `up` | rank +1 |
| `up-right diagonal` | file +1, rank +1 |
| `right` | file +1 |
| `right-down diagonal` | file +1, rank -1 |
| `down` | rank -1 |
| `down-left diagonal` | file -1, rank -1 |
| `left` | file -1 |
| `left-up diagonal` | file -1, rank +1 |

For example, from `c3`:

| Direction | Target |
|---|---|
| `up` | `c4` |
| `up-right diagonal` | `d4` |
| `right` | `d3` |
| `right-down diagonal` | `d2` |
| `down` | `c2` |
| `down-left diagonal` | `b2` |
| `left` | `b3` |
| `left-up diagonal` | `b4` |

---

## 6. Initial Positions

At the beginning of each sub-game:

- the Cop starts on one cell;
- the Robber starts on one cell;
- the two starting cells must be different;
- the Cop and Robber may not start on the same cell;
- both starting positions are known to both players before the first move.

Initial positions must be chosen randomly by a fair mutually agreed random process.

The initial position selection must produce disjoint legal cells.

Example:

```text
move 0: Cc4
move 0: Ra1
```

This means the Cop starts on `c4`, and the Robber starts on `a1`.

---

## 7. Rounds and Turn Order

### 7.1 Turn order

The Robber acts first.

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

### 7.2 Round limit

Each sub-game lasts at most **25 full rounds**.

Therefore, a sub-game has at most:

- 25 Robber actions;
- 25 Cop actions.

If the Cop completes the action of round 25 and no earlier terminal condition has occurred, the Robber wins by survival.

---

## 8. Actions

### 8.1 Robber actions

On each Robber turn, the Robber must move exactly one adjacent cell.

The Robber cannot pass.

The Robber cannot place blocks.

### 8.2 Cop actions

On each Cop turn, the Cop must choose exactly one legal action:

1. move exactly one adjacent cell; or
2. place a block on the Cop's current cell.

The Cop cannot pass.

The Cop cannot both move and place a block in the same turn.

---

## 9. Movement Rules

### 9.1 One adjacent cell

A movement action moves the acting player to exactly one adjacent cell.

Movement may be:

- vertical;
- horizontal;
- diagonal.

### 9.2 Legal movement directions

The only legal movement directions are:

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

### 9.3 Legal movement target

A movement target is legal only if:

- the target cell is inside the board;
- the target cell is not blocked.

### 9.4 Diagonal movement and corner-cutting

Diagonal movement is allowed.

Diagonal corner-cutting is also allowed.

A diagonal move is legal if the diagonal target cell itself is inside the board and unblocked.

The two side-adjacent orthogonal cells do not matter.

Example:

```text
From c3 to d4 is legal if d4 is free,
even if c4 or d3 is blocked.
```

### 9.5 No passing

Neither player may pass.

A player that has a legal action must take a legal action.

A player that has no legal action loses, according to the terminal rules below.

---

## 10. Blocks / Barriers

### 10.1 Who may place blocks

Only the Cop may place blocks.

The Robber may not place blocks.

### 10.2 Maximum number of blocks

The Cop may place at most **5 blocks per sub-game**.

### 10.3 Block placement replaces movement

Placing a block is an alternative to movement.

On a Cop turn, the Cop must either:

- move one adjacent cell; or
- place one block on the Cop's current cell.

The Cop may not move and place a block in the same turn.

### 10.4 Block location

A block can only be placed on the cell where the Cop is currently standing.

The Cop may not place a block:

- on the Robber's current cell;
- on an arbitrary cell elsewhere on the board;
- on a cell that is already blocked;
- after already using all 5 blocks in the current sub-game.

### 10.5 Cop standing on a newly blocked cell

When the Cop places a block, the block is placed on the Cop's current cell.

The Cop is temporarily allowed to stand on that newly blocked cell until the Cop's next turn.

On the Cop's next turn:

- the Cop must move away from that blocked cell;
- the Cop may not place another block while standing on that blocked cell.

If the Cop cannot move away from the blocked cell on the next Cop turn, the Cop loses because the Cop has no legal action.

### 10.6 Block effect

A blocked cell is impassable to both players.

No player may enter a blocked cell.

A blocked cell acts like a wall or board boundary.

### 10.7 Block duration

Blocks are permanent until the end of the current sub-game.

Blocks reset between sub-games.

At the beginning of every new sub-game:

- there are no blocks on the board;
- the Cop's used block count is reset to 0.

---

## 11. Capture and Terminal Conditions

A sub-game ends immediately when any terminal condition occurs.

### 11.1 Cop captures the Robber

The Cop wins immediately if the Cop moves into the Robber's current cell.

Terminal reason:

```text
cop_capture
```

### 11.2 Robber moves into the Cop

The Robber loses immediately if the Robber moves into the Cop's current cell.

This is treated as a Cop win.

Terminal reason:

```text
robber_moved_into_cop
```

### 11.3 Robber has no legal move

If the Robber has no legal move on the Robber's turn, the Robber loses.

This is treated as a Cop win.

Terminal reason:

```text
robber_no_legal_move
```

### 11.4 Cop has no legal action

If the Cop has no legal action on the Cop's turn, the Cop loses.

This is treated as a Robber win.

A legal Cop action is either:

1. a legal movement action; or
2. a legal block placement action.

A block placement action is legal only if:

- the Cop has not already placed 5 blocks in the current sub-game;
- the Cop is not currently standing on a blocked cell;
- the Cop's current cell is not already blocked.

Terminal reason:

```text
cop_no_legal_action
```

### 11.5 Round limit reached

If round 25 is completed without capture, forced loss, illegal action, invalid action, timeout failure, or any other terminal condition, the Robber wins.

The survival condition is checked after the Cop's action in round 25.

Terminal reason:

```text
round_limit_reached
```

---

## 12. Illegal Actions

An illegal action immediately causes the acting player to lose.

### 12.1 Illegal Robber actions

The Robber loses immediately if the Robber:

- tries to pass;
- tries to place a block;
- moves outside the board;
- moves into a blocked cell;
- moves more than one cell;
- uses a non-supported direction;
- moves into the Cop's current cell.

Terminal reason is one of:

```text
robber_illegal_action
robber_moved_into_cop
```

### 12.2 Illegal Cop movement

The Cop loses immediately if the Cop moves:

- outside the board;
- into a blocked cell;
- more than one cell;
- using a non-supported direction.

Terminal reason:

```text
cop_illegal_action
```

### 12.3 Illegal Cop block placement

The Cop loses immediately if the Cop attempts to place a block when:

- the Cop has already placed 5 blocks in the current sub-game;
- the Cop is standing on an already blocked cell;
- the Cop tries to place the block anywhere other than the Cop's current cell;
- the Cop tries to combine block placement with movement;
- the Cop tries to place a block on an already blocked cell.

Terminal reason:

```text
cop_illegal_action
```

---

## 13. Action Communication Rules

The game is played through public natural-language action declarations.

### 13.1 Language

Action declarations must be written in English.

### 13.2 Required honesty

Players must honestly declare their chosen action.

Players may not:

- lie about their action;
- intentionally misrepresent the board state;
- intentionally misrepresent positions;
- intentionally misrepresent blocks;
- intentionally claim that an illegal action is legal;
- hide a loss condition;
- pretend not to have lost when a terminal condition has occurred.

Before the first sub-game starts, both players must explicitly agree to the rules and promise not to cheat or lie.

### 13.3 Canonical movement declarations

A valid movement declaration must unambiguously mean exactly one of:

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

Equivalent English wording is allowed only if the intended canonical direction is unambiguous.

### 13.4 Cop block declaration

A valid Cop block declaration must unambiguously mean:

```text
I place a block.
```

Equivalent English wording is allowed only if the intended action is unambiguous.

### 13.5 Loss admission

If a player has no legal action, the player must explicitly admit loss.

Canonical form:

```text
I've lost the game.
```

Equivalent English wording is allowed only if the admission is unambiguous.

### 13.6 Coordinates in messages

Players may include coordinates in action messages, but coordinates are non-authoritative.

The declared direction or declared block action determines the action.

Example:

```text
I move up to c4.
```

If the player is actually on `c2`, the declared direction `up` means the movement target is `c3`, not `c4`.

If the declared direction is legal, the move is interpreted by direction.

If the declared direction is illegal, the action is illegal.

Coordinates may be used for clarity and logging, but they do not override the declared action.

---

## 14. Invalid, Unclear, or Missing Action Messages

### 14.1 Invalid or unclear action message

If a player sends an invalid, unclear, malformed, contradictory, or unparseable action message, that player receives exactly one retry.

If the retry is still invalid or unclear, the acting player loses.

Terminal reasons:

```text
robber_invalid_action_retry_failed
cop_invalid_action_retry_failed
```

### 14.2 Timeout or no response

If a player does not respond within the agreed time limit, that player receives exactly one retry.

If the retry also times out or produces no valid response, the acting player loses.

Terminal reasons:

```text
robber_timeout_retry_failed
cop_timeout_retry_failed
```

### 14.3 Illegal action versus unclear action

Illegal action and unclear action are different:

- An **illegal action** is clear but violates the rules. It causes immediate loss.
- An **unclear action** cannot be reliably mapped to one legal or illegal action. It receives one retry.

Example of illegal action:

```text
I move up.
```

when moving up goes outside the board.

Example of unclear action:

```text
I go over there.
```

when no canonical direction can be inferred.

---

## 15. State Knowledge

Both players know:

- the agreed rules;
- the board size;
- both initial positions;
- all public action declarations;
- all previous blocks;
- the full public move history.

After the initial positions, players do not need to receive direct coordinate updates.

Each player must maintain the current board state from:

- initial positions;
- public action declarations;
- block placements;
- terminal events.

Because all actions are public and players are required to be honest, the complete state is reconstructible from the public history.

---

## 16. Game Record / Notation

Each player must maintain a complete game record.

The record must contain:

- initial Cop position;
- initial Robber position;
- every Robber action result;
- every Cop action result;
- every block placement;
- terminal reason;
- winner;
- score.

### 16.1 Symbols

| Symbol | Meaning |
|---|---|
| `C` | Cop |
| `R` | Robber |
| `#` | Block placed on the Cop's current cell |
| `move 0` | Initial position |
| `winner: C` | Cop wins |
| `winner: R` | Robber wins |

### 16.2 Initial position notation

Example:

```text
move 0: Re2
move 0: Ce4
```

This means:

- Robber starts on `e2`;
- Cop starts on `e4`.

### 16.3 Movement notation

Robber movement:

```text
move 1: Rd1
```

Cop movement:

```text
move 1: Cd5
```

### 16.4 Block notation

Cop block placement:

```text
move 1: Ce4#
```

This means:

- Cop is on `e4`;
- Cop places a block on `e4`;
- Cop remains on `e4` until the Cop's next turn;
- on the Cop's next turn, the Cop must move away.

### 16.5 Sample game record

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
score: C=20, R=5
```

---

## 17. Scoring

Each sub-game is scored independently.

### 17.1 Scoring table

| Sub-game result | Cop score | Robber score |
|---|---:|---:|
| Cop wins | 20 | 5 |
| Robber wins | 5 | 10 |

### 17.2 Cop win scoring

The Cop receives 20 points and the Robber receives 5 points if the Cop wins by any of the following:

- Cop captures the Robber;
- Robber moves into the Cop's cell;
- Robber has no legal move;
- Robber makes an illegal action;
- Robber fails the invalid/unclear action retry;
- Robber fails the timeout/no-response retry.

### 17.3 Robber win scoring

The Cop receives 5 points and the Robber receives 10 points if the Robber wins by any of the following:

- Robber survives through round 25;
- Cop has no legal action;
- Cop makes an illegal movement action;
- Cop makes an illegal block placement action;
- Cop fails the invalid/unclear action retry;
- Cop fails the timeout/no-response retry.

### 17.4 Full-game score

A full game contains 6 valid sub-games.

The final full-game score is the sum of the sub-game scores.

Because each participant plays 3 sub-games as Cop and 3 sub-games as Robber:

- maximum possible score for one participant is 90;
- minimum possible score for one participant is 30.

Maximum score example:

```text
3 Cop wins:    3 * 20 = 60
3 Robber wins: 3 * 10 = 30
Total:                 90
```

Minimum score example:

```text
3 Cop losses:    3 * 5 = 15
3 Robber losses: 3 * 5 = 15
Total:                  30
```

---

## 18. Valid Sub-games and Technical Failure

A full game requires 6 valid sub-games.

A sub-game is valid if it ends by one of the rule-defined terminal conditions in this document.

A sub-game that cannot be completed because of external technical failure is not counted as one of the 6 valid sub-games and must be replayed.

Technical failure is different from game-rule loss.

Examples of game-rule loss:

- illegal action;
- invalid action after retry;
- timeout/no-response after retry;
- no legal action.

Examples of external technical failure:

- communication system unavailable;
- process crash;
- service outage;
- corrupted or missing game history that prevents both players from reconstructing the game.

A technical-failure sub-game must be marked as canceled, not as a win or loss, unless the failure is specifically a timeout/no-response by the acting player under the agreed timeout rule.

---

## 19. Final Rule Summary

```text
Players: Cop (C) and Robber (R)
Pre-game agreement: required before the first sub-game
Ruleset hash: exact match required or the game does not start
Full game: 6 valid sub-games
Role balance: each participant plays 3 sub-games as Cop and 3 as Robber
Default board: 5x5 rectangular grid
Coordinates: chess-like, e.g. a1-e5
Wrap-around: no
Initial positions: random, legal, disjoint, known to both players
Turn order: Robber first, then Cop
Round limit: 25 full rounds
Movement: exactly one adjacent cell
Diagonals: allowed
Corner-cutting: allowed if target cell is free
Passing: forbidden
Robber action: must move
Cop action: must move or place a block
Blocks: Cop only, max 5 per sub-game
Block location: Cop's current cell only
Block duration: permanent until sub-game end
Block reset: yes, every sub-game
Capture: Cop moves into Robber's cell
Robber loses if: moves into Cop, has no legal move, illegal/invalid action, timeout failure
Cop loses if: has no legal action, illegal/invalid action, timeout failure
Round-limit winner: Robber
Communication: honest English natural-language action declarations
Coordinates in messages: allowed but non-authoritative
Scoring: Cop win = Cop 20 / Robber 5; Robber win = Cop 5 / Robber 10
Full-game score: sum over 6 valid sub-games
```
