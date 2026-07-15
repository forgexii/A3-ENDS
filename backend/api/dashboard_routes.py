from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy import (
    func
)

from sqlalchemy.orm import (
    Session
)

from backend.core.database import (
    get_db
)

from backend.models.detection import (
    Detection
)

router = APIRouter(

    prefix="/dashboard",

    tags=["Dashboard"]
)


# ==========================================
# DASHBOARD STATS
# ==========================================

@router.get("/stats")
def get_dashboard_stats(

    db: Session = Depends(
        get_db
    )

):

    detections = db.query(
        Detection
    ).all()

    total_flows = len(
        detections
    )

    total_alerts = len([

        d for d in detections

        if d.is_anomaly

    ])

    critical_incidents = len([

        d for d in detections

        if d.severity == "CRITICAL"

    ])

    active_connections = len(

        set(

            (

                d.source_ip,
                d.destination_ip

            )

            for d in detections

        )

    )

    threat_level = "LOW"

    if critical_incidents > 0:

        threat_level = "CRITICAL"

    elif total_alerts > 10:

        threat_level = "HIGH"

    elif total_alerts > 5:

        threat_level = "MEDIUM"

    return {

        "total_flows":
            total_flows,

        "active_connections":
            active_connections,

        "total_alerts":
            total_alerts,

        "critical_incidents":
            critical_incidents,

        "threat_level":
            threat_level,

        # Temporary values until
        # metrics subsystem is connected

        "detection_accuracy":
            99.1,

        "adwin_status":
            "STABLE"
    }


# ==========================================
# ATTACK DISTRIBUTION
# ==========================================

@router.get("/attacks")
def get_attack_distribution(

    db: Session = Depends(
        get_db
    )

):

    results = (

        db.query(

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

        for attack, count in results

        if attack is not None

    }


# ==========================================
# SEVERITY DISTRIBUTION
# ==========================================

@router.get("/severity")
def get_severity_distribution(

    db: Session = Depends(
        get_db
    )

):

    results = (

        db.query(

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

        for severity, count in results

        if severity is not None

    }