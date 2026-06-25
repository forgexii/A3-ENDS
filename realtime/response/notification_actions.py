"""
SOC Notifications and Alerting

Notifies security analysts and
external systems of threats.
"""

import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class NotificationActions:
    """Send alerts to SOC and external systems."""

    def __init__(self):
        self.notification_queue = []
        self.alert_channels = [
            "dashboard",
            "email",
            "slack",
            "siem"
        ]

    def send(
        self,
        detection: Dict
    ) -> Dict:
        """
        Send alert to all configured channels.
        
        Args:
            detection: Detection data to alert on
            
        Returns:
            Alert status dict
        """
        alert_id = self._generate_alert_id()
        
        alert_data = {
            "alert_id": alert_id,
            "severity": detection.get("severity", "UNKNOWN"),
            "attack_type": detection.get("attack_type", "Unknown"),
            "source_ip": detection.get("source_ip", "UNKNOWN"),
            "dest_ip": detection.get("dest_ip", "UNKNOWN"),
            "risk_score": detection.get("risk_score", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "channels_notified": []
        }
        
        # Notify all channels
        for channel in self.alert_channels:
            try:
                if channel == "dashboard":
                    self._notify_dashboard(alert_data)
                elif channel == "email":
                    self._notify_email(alert_data)
                elif channel == "slack":
                    self._notify_slack(alert_data)
                elif channel == "siem":
                    self._notify_siem(alert_data)
                
                alert_data["channels_notified"].append(channel)
            except Exception as e:
                logger.error(f"Failed to notify {channel}: {str(e)}")
        
        # Add to notification queue
        self.notification_queue.append(alert_data)
        
        logger.warning(
            f"[ALERT] ID: {alert_id} | Severity: {alert_data['severity']} | "
            f"Attack: {alert_data['attack_type']} | "
            f"Score: {alert_data['risk_score']:.2f}"
        )
        
        return {
            "status": "sent",
            "alert_id": alert_id,
            "channels": alert_data["channels_notified"],
            "timestamp": alert_data["timestamp"]
        }

    def _notify_dashboard(self, alert_data: Dict):
        """Notify dashboard (real-time UI update)."""
        logger.info(f"Dashboard notification: {alert_data['alert_id']}")

    def _notify_email(self, alert_data: Dict):
        """Send email notification."""
        # In production, send actual email
        logger.info(
            f"Email notification sent: Severity {alert_data['severity']} "
            f"- {alert_data['attack_type']}"
        )

    def _notify_slack(self, alert_data: Dict):
        """Send Slack notification."""
        # In production, post to Slack webhook
        logger.info(f"Slack notification sent: {alert_data['alert_id']}")

    def _notify_siem(self, alert_data: Dict):
        """Forward to SIEM system."""
        # In production, forward to SIEM
        logger.info(f"SIEM forwarded: {alert_data['alert_id']}")

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        from datetime import datetime
        import random
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        rand_suffix = random.randint(1000, 9999)
        return f"ALERT-{timestamp}-{rand_suffix}"

    def get_notifications(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent notifications."""
        return self.notification_queue[-limit:]