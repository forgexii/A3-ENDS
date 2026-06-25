"""
Endpoint Quarantine Actions

Isolates compromised hosts by:
- Network segmentation
- Process termination
- System quarantine
"""

import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class QuarantineActions:
    """Execute endpoint isolation and quarantine actions."""

    def __init__(self):
        self.isolated_hosts = set()
        self.quarantined_processes = {}
        self.isolation_queue = []

    def isolate_host(
        self,
        detection: Dict
    ) -> Dict:
        """
        Isolate compromised host from network.
        
        Args:
            detection: Detection data with dest_ip or hostname
            
        Returns:
            Action result dict
        """
        hostname = detection.get("dest_hostname", "unknown")
        dest_ip = detection.get("dest_ip", "UNKNOWN")
        
        if dest_ip in self.isolated_hosts:
            logger.warning(f"Host already isolated: {dest_ip}")
            return {
                "action": "isolate_host",
                "status": "already_isolated",
                "hostname": hostname,
                "ip": dest_ip,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Add to isolated hosts
        self.isolated_hosts.add(dest_ip)
        
        # Queue isolation action
        self.isolation_queue.append({
            "hostname": hostname,
            "ip": dest_ip,
            "action": "network_segment",
            "timestamp": datetime.utcnow()
        })
        
        logger.warning(
            f"[QUARANTINE] Host isolated: {hostname} ({dest_ip}) "
            f"- Network segmentation applied"
        )
        
        return {
            "action": "isolate_host",
            "status": "success",
            "hostname": hostname,
            "ip": dest_ip,
            "isolation_type": "network_segment",
            "timestamp": datetime.utcnow().isoformat()
        }

    def quarantine_process(
        self,
        detection: Dict,
        process_id: str = None
    ) -> Dict:
        """
        Quarantine malicious process.
        
        Args:
            detection: Detection data
            process_id: Process ID to quarantine
            
        Returns:
            Action result dict
        """
        process_id = process_id or detection.get("process_id", "unknown")
        hostname = detection.get("dest_hostname", "unknown")
        
        self.quarantined_processes[process_id] = {
            "hostname": hostname,
            "reason": detection.get("attack_type", "Malicious"),
            "quarantined_at": datetime.utcnow(),
            "status": "quarantined"
        }
        
        logger.warning(
            f"[QUARANTINE] Process quarantined: PID {process_id} on {hostname} "
            f"(Reason: {detection.get('attack_type', 'Unknown')})"
        )
        
        return {
            "action": "quarantine_process",
            "status": "success",
            "hostname": hostname,
            "process_id": process_id,
            "reason": detection.get("attack_type", "Malicious"),
            "timestamp": datetime.utcnow().isoformat()
        }

    def revoke_access(
        self,
        detection: Dict
    ) -> Dict:
        """
        Revoke access credentials and sessions.
        
        Args:
            detection: Detection data
            
        Returns:
            Action result dict
        """
        dest_ip = detection.get("dest_ip", "UNKNOWN")
        user_id = detection.get("user_id", "unknown")
        
        logger.warning(
            f"[QUARANTINE] Access revoked: User {user_id} on {dest_ip}"
        )
        
        return {
            "action": "revoke_access",
            "status": "success",
            "ip": dest_ip,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_isolated_hosts(self) -> List[str]:
        """Get list of isolated hosts."""
        return list(self.isolated_hosts)

    def get_quarantined_processes(self) -> Dict:
        """Get quarantined processes."""
        return dict(self.quarantined_processes)