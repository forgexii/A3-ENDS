"""
RL Policy Engine

Manages Q-Learning based adaptive policy:
- Learns from detection outcomes
- Learns from false alarms
- Learns from drift
- Improves response decisions over time
"""

import logging
from typing import Dict
from realtime.rl.q_learning_agent import QLearningAgent

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Manage adaptive RL-based response policy."""

    def __init__(self):
        self.agent = QLearningAgent()
        self.learning_history = []

    def decide(
        self,
        detection: Dict
    ) -> Dict:
        """
        Get RL-based action recommendation.
        
        Args:
            detection: Detection data with severity and drift info
            
        Returns:
            RL decision with state and recommended action
        """
        severity = detection.get("severity", "LOW")
        drift = detection.get("drift_detected", False)

        state = self.agent.get_state_key(severity, drift)
        action = self.agent.choose_action(state)

        return {
            "rl_state": state,
            "recommended_action": action,
            "severity": severity,
            "drift": drift
        }

    def learn_from_detection(
        self,
        detection: Dict,
        outcome: str = "true_positive"
    ):
        """
        Learn from successful detection.
        
        Args:
            detection: Detection data
            outcome: "true_positive" or "true_negative"
        """
        severity = detection.get("severity", "LOW")
        state = self.agent.get_state_key(severity, False)
        
        # Reward based on outcome
        reward = 1.0 if outcome == "true_positive" else -0.5
        
        # Update Q-value
        self.agent.update_q_value(state, "execute", reward)
        
        logger.info(f"[RL] Learning from {outcome}: state={state}, reward={reward}")
        
        self.learning_history.append({
            "type": "detection",
            "outcome": outcome,
            "state": state,
            "reward": reward
        })

    def learn_from_false_alarm(
        self,
        detection: Dict
    ):
        """
        Learn from false alarm to improve accuracy.
        
        Applies negative reward to discourage similar detections.
        
        Args:
            detection: False alarm detection data
        """
        severity = detection.get("severity", "LOW")
        state = self.agent.get_state_key(severity, False)
        
        # Negative reward for false alarm
        reward = -1.0
        
        # Update Q-value to penalize this state-action pair
        self.agent.update_q_value(state, "execute", reward)
        
        logger.warning(
            f"[RL] Learning from false alarm: state={state}, reward={reward}"
        )
        
        self.learning_history.append({
            "type": "false_alarm",
            "state": state,
            "reward": reward
        })

    def learn_from_drift(
        self,
        detection: Dict,
        drift_value: float
    ):
        """
        Learn from concept drift.
        
        Updates policy when model drift is detected.
        
        Args:
            detection: Detection data
            drift_value: ADWIN drift estimation value
        """
        severity = detection.get("severity", "LOW")
        state = self.agent.get_state_key(severity, True)  # Drift detected
        
        # Moderate negative reward for drift
        reward = -0.5 + (drift_value * 0.5)  # Scale with drift magnitude
        
        # Update Q-value to adapt to drift
        self.agent.update_q_value(state, "update_model", reward)
        
        logger.warning(
            f"[RL] Learning from drift: state={state}, drift={drift_value}, reward={reward}"
        )
        
        self.learning_history.append({
            "type": "drift",
            "state": state,
            "drift_value": drift_value,
            "reward": reward
        })

    def learn_from_analyst_decision(
        self,
        detection: Dict,
        decision: str  # "approve", "reject", "investigate"
    ):
        """
        Learn from analyst decisions.
        
        Improves correlation between automatic decisions and analyst judgment.
        
        Args:
            detection: Detection data
            decision: Analyst's decision
        """
        severity = detection.get("severity", "LOW")
        state = self.agent.get_state_key(severity, False)
        
        # Reward based on analyst decision alignment
        if decision == "approve":
            reward = 1.0  # Model was correct
        elif decision == "reject":
            reward = -1.0  # False alarm - model was wrong
        else:  # investigate
            reward = 0.0  # Inconclusive
        
        self.agent.update_q_value(state, "execute", reward)
        
        logger.info(
            f"[RL] Learning from analyst decision '{decision}': "
            f"state={state}, reward={reward}"
        )
        
        self.learning_history.append({
            "type": "analyst_feedback",
            "decision": decision,
            "state": state,
            "reward": reward
        })

    def get_policy_stats(self) -> Dict:
        """Get current policy statistics."""
        return {
            "q_table": self.agent.q_table,
            "total_updates": len(self.learning_history),
            "learning_history": self.learning_history[-100:]  # Last 100 updates
        }

    def export_model(self) -> Dict:
        """Export current model for persistence."""
        return {
            "q_table": self.agent.q_table,
            "state_action_counts": self.agent.state_action_counts
        }

    def import_model(self, model_data: Dict):
        """Import previously saved model."""
        self.agent.q_table = model_data.get("q_table", {})
        self.agent.state_action_counts = model_data.get("state_action_counts", {})