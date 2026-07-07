"""
Q-Learning Agent

Tabular Q-learning for adaptive NIDS response policy.
The Q-table is persisted to a JSON file on every update and
reloaded on startup so policy is not lost between process restarts.

State space: (severity, drift_detected)
Action space: [MONITOR, NOTIFY, BLOCK, QUARANTINE]
"""

import json
import logging
import random
from pathlib import Path

from backend.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Persist Q-table in the realtime/rl directory (user-writable)
_Q_TABLE_PATH: Path = PROJECT_ROOT / "realtime" / "rl" / "q_table.json"


def _tuple_key(state) -> str:
    """JSON keys must be strings; serialise tuple as 'severity|drift'."""
    return f"{state[0]}|{state[1]}"


def _load_q_table() -> dict:
    _Q_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _Q_TABLE_PATH.exists():
        try:
            with open(_Q_TABLE_PATH, "r") as f:
                raw = json.load(f)
            # Convert string keys back to tuples
            q = {}
            for k, v in raw.items():
                parts = k.split("|", 1)
                if len(parts) == 2:
                    drift = parts[1] == "True"
                    q[(parts[0], drift)] = v
            logger.info(f"[QLearning] Loaded Q-table ({len(q)} states) from {_Q_TABLE_PATH}")
            return q
        except Exception as exc:
            logger.warning(f"[QLearning] Could not load Q-table: {exc}")
    return {}


def _save_q_table(q_table: dict):
    try:
        _Q_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
        serialisable = {_tuple_key(k): v for k, v in q_table.items()}
        with open(_Q_TABLE_PATH, "w") as f:
            json.dump(serialisable, f, indent=2)
    except Exception as exc:
        logger.warning(f"[QLearning] Could not save Q-table: {exc}")


class QLearningAgent:

    ACTIONS = ["MONITOR", "NOTIFY", "BLOCK", "QUARANTINE"]

    def __init__(self):
        self.alpha   = 0.1    # learning rate
        self.gamma   = 0.9    # discount factor
        self.epsilon = 0.1    # exploration rate

        self.q_table: dict               = _load_q_table()
        self.state_action_counts: dict   = {}

    # ==========================================
    # STATE KEY
    # ==========================================

    def get_state_key(self, severity: str, drift: bool):
        return (severity, bool(drift))

    # ==========================================
    # ACTION SELECTION
    # ==========================================

    def choose_action(self, state) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.ACTIONS)

        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.ACTIONS}

        return max(self.q_table[state], key=self.q_table[state].get)

    # ==========================================
    # Q-VALUE UPDATE  (persists after every update)
    # ==========================================

    def update_q_value(self, state, action: str, reward: float):
        """Direct Q-value update (used by PolicyEngine for simple feedback)."""
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.ACTIONS}

        old_q = self.q_table[state].get(action, 0.0)
        # Simple moving-average update (no next-state for direct feedback)
        self.q_table[state][action] = old_q + self.alpha * (reward - old_q)

        # Track call count
        key = f"{state}|{action}"
        self.state_action_counts[key] = self.state_action_counts.get(key, 0) + 1

        _save_q_table(self.q_table)

    def update(self, state, action: str, reward: float, next_state):
        """Full Bellman update (used when next-state is known)."""
        for s in (state, next_state):
            if s not in self.q_table:
                self.q_table[s] = {a: 0.0 for a in self.ACTIONS}

        current_q   = self.q_table[state].get(action, 0.0)
        max_future  = max(self.q_table[next_state].values())
        new_q       = current_q + self.alpha * (reward + self.gamma * max_future - current_q)
        self.q_table[state][action] = new_q

        _save_q_table(self.q_table)