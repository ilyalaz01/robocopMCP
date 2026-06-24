# PRD — Q-Learning (tabular)

**Version 1.00.** RL depth the professor expects (SPEC §9). Backs `suggest_move`.

## Background
Tabular Q-learning learns an action-value `Q(s,a)` via the Bellman update. Movement
strategy is the Q-table's job; language is the LLM's job — they do not compete.

## State encoding `s`
Relative displacement `(dx, dy)` between the agent's cell and the **believed** opponent
cell, clamped to grid bounds, optionally with a coarse barrier feature. Relative encoding
shrinks the table and generalizes across the board. The believed cell comes from
observation (if visible) or the language-derived belief.

## Action space `a`
The 8 `MOVE_DIRECTIONS`; the Cop additionally has `PLACE_BARRIER`.

## Reward `r` (config / constants)
- **Cop:** `step_penalty` (−1) each step, `+capture_reward` (50) on capture.
- **Thief:** `+survive_reward` (1) per surviving step, `−capture_reward` on capture.

## Update rule
`Q(s,a) ← Q(s,a) + α·[ r + γ·max_a' Q(s',a') − Q(s,a) ]`, with ε-greedy exploration and
`epsilon_decay` toward `min_epsilon`. Params from `config.q_learning`.

## Training
`trainer.py` runs **offline self-play** (no LLM, no network) to populate **separate** Cop
and Thief Q-tables, saving them and **reward-per-episode** to `results/` for learning
curves. A **heuristic baseline** (Chebyshev-distance greedy policy) is the comparison.

## Success criteria
Reward trend improves over episodes; Q-tables saved; update-rule and policy unit-tested;
Q-policy beats or matches the heuristic baseline in the notebook.
