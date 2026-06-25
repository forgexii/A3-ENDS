"""
Firewall Response Actions

Executes dynamic response actions:
- Block IP (add to firewall blocklist)
- Rate limiting (throttle connections)
- Connection termination
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)


class FirewallActions:
    """Execute firewall-level response actions."""

    def __init__(self):
        self.blocked_ips = set()
        self.rate_limited_ips = {}
        self.blocked_ports = set()
        self.termination_queue = []

    def block_ip(
        self,
        detection: Dict
    ) -> Dict:
        """
        Block malicious IP address.
        
        Args:
            detection: Detection data with source_ip
            
        Returns:
            Action result dict
        """
        source_ip = detection.get("source_ip", "UNKNOWN")
        
        if source_ip in self.blocked_ips:
            logger.warning(f"IP already blocked: {source_ip}")
            return {
                "action": "block_ip",
                "status": "already_blocked",
                "ip": source_ip,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Add to blocklist
        self.blocked_ips.add(source_ip)
        
        # Log action
        logger.warning(
            f"[FIREWALL] Blocked IP: {source_ip} "
            f"(Attack: {detection.get('attack_type', 'Unknown')})"
        )
        
        return {
            "action": "block_ip",
            "status": "success",
            "ip": source_ip,
            "ttl": 3600,  # Block for 1 hour
            "timestamp": datetime.utcnow().isoformat()
        }

    def rate_limit(
        self,
        detection: Dict,
        max_connections: int = 10,
        window_seconds: int = 60
    ) -> Dict:
        """
        Apply rate limiting to source IP.
        
        Args:
            detection: Detection data
            max_connections: Max connections per window
            window_seconds: Time window for rate limit
            
        Returns:
            Action result dict
        """
        source_ip = detection.get("source_ip", "UNKNOWN")
        
        self.rate_limited_ips[source_ip] = {
            "max_connections": max_connections,
            "window_seconds": window_seconds,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=window_seconds * 10)
        }
        
        logger.warning(
            f"[FIREWALL] Rate limit applied to {source_ip}: "
            f"{max_connections} conn/{window_seconds}s"
        )
        
        return {
            "action": "rate_limit",
            "status": "success",
            "ip": source_ip,
            "max_connections": max_connections,
            "window_seconds": window_seconds,
            "timestamp": datetime.utcnow().isoformat()
        }

    def terminate_connections(
        self,
        detection: Dict
    ) -> Dict:
        """
        Terminate existing connections from malicious IP.
        
        Args:
            detection: Detection data
            
        Returns:
            Action result dict
        """
        source_ip = detection.get("source_ip", "UNKNOWN")
        port = detection.get("port", 0)
        
        self.termination_queue.append({
            "source_ip": source_ip,
            "port": port,
            "timestamp": datetime.utcnow()
        })
        
        logger.warning(
            f"[FIREWALL] Terminating connections from {source_ip}:{port}"
        )
        
        return {
            "action": "terminate_connections",
            "status": "success",
            "ip": source_ip,
            "port": port,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs."""
        return list(self.blocked_ips)

    def get_rate_limited_ips(self) -> Dict:
        """Get rate-limited IPs and their rules."""
        return dict(self.rate_limited_ips)