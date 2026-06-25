"""
Response Engine

Orchestrates automated response actions:
- Firewall actions (block, rate limit, terminate)
- Host quarantine (isolate, segment, revoke access)
- Notifications (SOC, SIEM, email, Slack)

Supports analyst approval workflows.
"""

import logging
from datetime import datetime
from typing import Dict, List

from realtime.response.firewall_actions import FirewallActions
from realtime.response.notification_actions import NotificationActions
from realtime.response.quarantine_actions import QuarantineActions

logger = logging.getLogger(__name__)


class ResponseEngine:
    """Orchestrate response actions based on threat severity."""

    def __init__(self):
        self.firewall = FirewallActions()
        self.notifications = NotificationActions()
        self.quarantine = QuarantineActions()
        self.response_history = []

    def execute(
        self,
        detection: Dict,
        approved: bool = False
    ) -> Dict:
        """
        Execute response actions based on severity.
        
        Args:
            detection: Detection data with severity and response_actions
            approved: Whether analyst approved the response
            
        Returns:
            Response execution result
        """
        severity = detection.get("severity", "LOW")
        attack_type = detection.get("attack_type", "Unknown")
        
        result = {
            "detection_id": detection.get("id", "unknown"),
            "severity": severity,
            "approved": approved,
            "timestamp": datetime.utcnow().isoformat(),
            "actions_executed": []
        }
        
        # Always notify
        notify_result = self.notifications.send(detection)
        result["actions_executed"].append("notification")
        
        # Severity-based response
        if severity == "LOW":
            # Just log - no automated action
            logger.info(
                f"[RESPONSE] Low severity {attack_type} - logging only"
            )
            result["action_level"] = "log_only"
            
        elif severity == "MEDIUM":
            # Request analyst review
            logger.warning(
                f"[RESPONSE] Medium severity {attack_type} - waiting for analyst"
            )
            result["action_level"] = "analyst_review"
            if approved:
                block_result = self.firewall.block_ip(detection)
                result["actions_executed"].append("block_ip")
                
        elif severity == "HIGH":
            # Escalate and execute response
            logger.critical(
                f"[RESPONSE] High severity {attack_type} - escalating"
            )
            result["action_level"] = "escalate"
            
            # Execute response actions
            block_result = self.firewall.block_ip(detection)
            result["actions_executed"].append("block_ip")
            
            rate_result = self.firewall.rate_limit(detection)
            result["actions_executed"].append("rate_limit")
            
        elif severity == "CRITICAL":
            # Immediate comprehensive response
            logger.critical(
                f"[RESPONSE] CRITICAL severity {attack_type} - immediate response"
            )
            result["action_level"] = "immediate_response"
            
            # Execute all response actions
            block_result = self.firewall.block_ip(detection)
            result["actions_executed"].append("block_ip")
            
            rate_result = self.firewall.rate_limit(detection, max_connections=1)
            result["actions_executed"].append("rate_limit")
            
            terminate_result = self.firewall.terminate_connections(detection)
            result["actions_executed"].append("terminate_connections")
            
            isolate_result = self.quarantine.isolate_host(detection)
            result["actions_executed"].append("isolate_host")
        
        # Record in history
        self.response_history.append(result)
        
        return result

    def get_suggested_actions(
        self,
        severity: str,
        attack_type: str
    ) -> List[str]:
        """
        Get suggested response actions for severity.
        
        Args:
            severity: Threat severity level
            attack_type: Type of attack detected
            
        Returns:
            List of suggested actions
        """
        actions = []
        
        if severity in ["HIGH", "CRITICAL"]:
            actions.extend([
                "Block source IP",
                "Rate limit connections"
            ])
        
        if severity == "CRITICAL":
            actions.extend([
                "Isolate destination host",
                "Terminate active connections",
                "Revoke access credentials"
            ])
        
        if attack_type == "BOTNET":
            actions.append("Quarantine infected host")
        
        if attack_type in ["WEB_ATTACK", "INFILTRATION"]:
            actions.append("Revoke user access")
        
        return actions

    def get_response_history(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """Get response execution history."""
        return self.response_history[-limit:]