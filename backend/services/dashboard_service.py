"""
Dashboard Service

Provides realtime SOC metrics
for the frontend dashboard.
"""

from datetime import datetime
from datetime import timedelta

from sqlalchemy import func

from backend.core.database import (
    SessionLocal
)

from backend.models.detection import (
    Detection
)


class DashboardService:

    def __init__(self):

        self.db = SessionLocal()

    # ==========================================
    # DASHBOARD STATS
    # ==========================================

    def get_stats(self):

        total_flows = (

            self.db.query(
                Detection
            ).count()

        )

        total_alerts = (

            self.db.query(
                Detection
            )
            .filter(
                Detection.is_anomaly == True
            )
            .count()

        )

        critical_count = (

            self.db.query(
                Detection
            )
            .filter(
                Detection.severity == "CRITICAL"
            )
            .count()

        )

        active_conns = (

            self.db.query(

                func.count(
                    Detection.source_ip
                )

            )
            .scalar()

        )

        threat_level = "LOW"

        if critical_count > 20:

            threat_level = "HIGH"

        elif critical_count > 5:

            threat_level = "MEDIUM"

        return {

            "total_flows":
                total_flows,

            "active_conns":
                active_conns,

            "total_alerts":
                total_alerts,

            "critical_count":
                critical_count,

            "threat_level":
                threat_level
        }

    # ==========================================
    # ATTACK DISTRIBUTION
    # ==========================================

    def attack_distribution(self):

        rows = (

            self.db.query(

                Detection.attack_type,

                func.count(
                    Detection.id
                )

            )

            .group_by(
                Detection.attack_type
            )

            .all()

        )

        return {

            attack: count

            for attack, count in rows

            if attack is not None
        }

    # ==========================================
    # SEVERITY DISTRIBUTION
    # ==========================================

    def severity_distribution(self):

        rows = (

            self.db.query(

                Detection.severity,

                func.count(
                    Detection.id
                )

            )

            .group_by(
                Detection.severity
            )

            .all()

        )

        return {

            severity: count

            for severity, count in rows

            if severity is not None
        }

    # ==========================================
    # LAST 24 HOURS
    # ==========================================

    def detections_last_24h(self):

        since = (

            datetime.utcnow()

            -

            timedelta(hours=24)
        )

        return (

            self.db.query(
                Detection
            )

            .filter(
                Detection.timestamp >= since
            )

            .count()

        )