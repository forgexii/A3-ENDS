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

    prefix="/analytics",

    tags=["Analytics"]
)


# ==========================================
# RECENT DETECTIONS
# ==========================================

@router.get("/recent")
def get_recent_detections(

    limit: int = 50,

    db: Session = Depends(
        get_db
    )

):

    detections = (

        db.query(
            Detection
        )

        .order_by(
            Detection.timestamp.desc()
        )

        .limit(limit)

        .all()

    )

    return detections


# ==========================================
# TOP SOURCE IPS
# ==========================================

@router.get("/top-sources")
def get_top_sources(

    limit: int = 10,

    db: Session = Depends(
        get_db
    )

):

    results = (

        db.query(

            Detection.source_ip,

            func.count(
                Detection.id
            ).label("count")

        )

        .group_by(
            Detection.source_ip
        )

        .order_by(
            func.count(
                Detection.id
            ).desc()
        )

        .limit(limit)

        .all()

    )

    return [

        {

            "source_ip":
                row[0],

            "count":
                row[1]

        }

        for row in results

    ]


# ==========================================
# TOP TARGETS
# ==========================================

@router.get("/top-targets")
def get_top_targets(

    limit: int = 10,

    db: Session = Depends(
        get_db
    )

):

    results = (

        db.query(

            Detection.destination_ip,

            func.count(
                Detection.id
            ).label("count")

        )

        .group_by(
            Detection.destination_ip
        )

        .order_by(
            func.count(
                Detection.id
            ).desc()
        )

        .limit(limit)

        .all()

    )

    return [

        {

            "destination_ip":
                row[0],

            "count":
                row[1]

        }

        for row in results

    ]


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

    return [

        {

            "attack_type":
                attack,

            "count":
                count

        }

        for attack, count in results

        if attack is not None

    ]


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

    return [

        {

            "severity":
                severity,

            "count":
                count

        }

        for severity, count in results

        if severity is not None

    ]