"""
Detection Routes
"""

from typing import List

from fastapi import (

    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from backend.core.database import (
    get_db
)

from backend.schemas.detection_schema import (
    DetectionResponse
)

from backend.services.detection_service import (
    detection_service
)

router = APIRouter()


# ==========================================
# GET DETECTIONS
# ==========================================

@router.get(

    "/detections",

    response_model=
        List[
            DetectionResponse
        ]
)

def get_detections(

    limit: int = 100,

    db: Session = Depends(
        get_db
    )

):

    return (

        detection_service
        .get_detections(

            db,

            limit

        )

    )


# ==========================================
# GET DETECTION
# ==========================================

@router.get(

    "/detections/{detection_id}",

    response_model=
        DetectionResponse
)

def get_detection(

    detection_id: int,

    db: Session = Depends(
        get_db
    )

):

    detection = (

        detection_service
        .get_detection(

            db,

            detection_id

        )

    )

    if detection is None:

        raise HTTPException(

            status_code=404,

            detail="Detection not found"
        )

    return detection


# ==========================================
# ALERTS
# ==========================================

@router.get(

    "/alerts",

    response_model=
        List[
            DetectionResponse
        ]
)

def get_alerts(

    limit: int = 100,

    db: Session = Depends(
        get_db
    )

):

    return (

        detection_service
        .get_alerts(

            db,

            limit

        )

    )


# ==========================================
# DASHBOARD
# ==========================================

@router.get(
    "/dashboard/stats"
)

def dashboard_stats(

    db: Session = Depends(
        get_db
    )

):

    return (

        detection_service
        .dashboard_stats(
            db
        )

    )