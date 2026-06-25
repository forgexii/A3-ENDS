"""
Detection Service
"""

from sqlalchemy.orm import Session

from backend.models.detection import (
    Detection
)


class DetectionService:

    # ==========================================
    # CREATE DETECTION
    # ==========================================

    def create_detection(
        self,
        db: Session,
        detection_data: dict
    ):

        detection = Detection(

            source_ip=
                detection_data["source_ip"],

            destination_ip=
                detection_data["destination_ip"],

            source_port=
                detection_data["source_port"],

            destination_port=
                detection_data["destination_port"],

            protocol=
                detection_data["protocol"],

            anomaly_score=
                detection_data["anomaly_score"],

            threshold=
                detection_data["threshold"],

            is_anomaly=
                detection_data["is_anomaly"],

            classification=
                detection_data.get(
                    "classification"
                ),

            attack_type=
                detection_data.get(
                    "attack_type"
                ),

            confidence=
                detection_data.get(
                    "confidence"
                ),

            severity=
                detection_data.get(
                    "severity"
                ),

            risk_score=
                detection_data.get(
                    "risk_score"
                )
        )

        db.add(
            detection
        )

        db.commit()

        db.refresh(
            detection
        )

        return detection

    # ==========================================
    # GET DETECTION
    # ==========================================

    def get_detection(
        self,
        db: Session,
        detection_id: int
    ):

        return (

            db.query(
                Detection
            )

            .filter(
                Detection.id ==
                detection_id
            )

            .first()

        )

    # ==========================================
    # LIST DETECTIONS
    # ==========================================

    def get_detections(
        self,
        db: Session,
        limit: int = 100
    ):

        return (

            db.query(
                Detection
            )

            .order_by(
                Detection.timestamp.desc()
            )

            .limit(limit)

            .all()

        )

    # ==========================================
    # ALERTS ONLY
    # ==========================================

    def get_alerts(
        self,
        db: Session,
        limit: int = 100
    ):

        return (

            db.query(
                Detection
            )

            .filter(
                Detection.is_anomaly == True
            )

            .order_by(
                Detection.timestamp.desc()
            )

            .limit(limit)

            .all()

        )

    # ==========================================
    # DASHBOARD STATS
    # ==========================================

    def dashboard_stats(
        self,
        db: Session
    ):

        total = (

            db.query(
                Detection
            )

            .count()

        )

        alerts = (

            db.query(
                Detection
            )

            .filter(
                Detection.is_anomaly == True
            )

            .count()

        )

        critical = (

            db.query(
                Detection
            )

            .filter(
                Detection.severity ==
                "CRITICAL"
            )

            .count()

        )

        high = (

            db.query(
                Detection
            )

            .filter(
                Detection.severity ==
                "HIGH"
            )

            .count()

        )

        return {

            "total_flows":
                total,

            "alerts":
                alerts,

            "critical":
                critical,

            "high":
                high
        }


detection_service = (
    DetectionService()
)