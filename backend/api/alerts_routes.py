"""
Alerts Routes - Frontend Integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from backend.core.database import get_db
from backend.models.alert import Alert, AlertStatus, AlertSeverity
from backend.schemas.alert_schema import (
    AlertResponse,
    AlertListResponse,
    AlertDetailResponse,
    AlertUpdateRequest,
)
import json

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.get("/", response_model=AlertListResponse)
def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: str = Query(None),
    status: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated alerts with filtering"""
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if status:
        query = query.filter(Alert.status == status)
    
    if search:
        query = query.filter(
            (Alert.source_ip.ilike(f"%{search}%")) |
            (Alert.destination_ip.ilike(f"%{search}%")) |
            (Alert.attack_type.ilike(f"%{search}%"))
        )
    
    total = query.count()
    alerts = query.order_by(Alert.timestamp.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    alert_responses = []
    for alert in alerts:
        alert_responses.append(
            AlertResponse(
                id=alert.id,
                ts=alert.timestamp.strftime("%H:%M:%S"),
                src_ip=alert.source_ip,
                dst_ip=alert.destination_ip,
                protocol=alert.protocol,
                attack=alert.attack_type,
                severity=alert.severity,
                risk=int(alert.risk_score),
                conf=int(alert.confidence),
                status=alert.status,
                timestamp=alert.timestamp,
                source_port=alert.source_port,
                destination_port=alert.destination_port,
                anomaly_score=alert.anomaly_score,
                classification_confidence=alert.classification_confidence,
                shap_explanation=json.loads(alert.shap_explanation) if alert.shap_explanation else None,
            )
        )
    
    return AlertListResponse(
        alerts=alert_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{alert_id}", response_model=AlertDetailResponse)
def get_alert_detail(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed alert information"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert_response = AlertResponse(
        id=alert.id,
        ts=alert.timestamp.strftime("%H:%M:%S"),
        src_ip=alert.source_ip,
        dst_ip=alert.destination_ip,
        protocol=alert.protocol,
        attack=alert.attack_type,
        severity=alert.severity,
        risk=int(alert.risk_score),
        conf=int(alert.confidence),
        status=alert.status,
        timestamp=alert.timestamp,
        source_port=alert.source_port,
        destination_port=alert.destination_port,
        anomaly_score=alert.anomaly_score,
        classification_confidence=alert.classification_confidence,
        shap_explanation=json.loads(alert.shap_explanation) if alert.shap_explanation else None,
    )
    
    # Get related alerts (same source IP or within time window)
    time_window = alert.timestamp - timedelta(minutes=5)
    related_alerts = db.query(Alert).filter(
        Alert.source_ip == alert.source_ip,
        Alert.timestamp >= time_window,
        Alert.id != alert_id
    ).all()
    
    return AlertDetailResponse(
        alert=alert_response,
        timeline=[],  # Can be enhanced with event timeline
        indicators=[alert.source_ip, alert.destination_ip],
        mitre_tactics=[]  # Can be populated from attack classification
    )


@router.put("/{alert_id}")
def update_alert(
    alert_id: str,
    update_request: AlertUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update alert status and notes"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = update_request.status
    if update_request.notes:
        alert.notes = update_request.notes
    alert.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    return {"status": "success", "message": "Alert updated"}


@router.get("/stats/summary")
def get_alerts_summary(
    db: Session = Depends(get_db)
):
    """Get alert statistics summary"""
    total_alerts = db.query(Alert).count()
    critical = db.query(Alert).filter(Alert.severity == AlertSeverity.CRITICAL.value).count()
    high = db.query(Alert).filter(Alert.severity == AlertSeverity.HIGH.value).count()
    medium = db.query(Alert).filter(Alert.severity == AlertSeverity.MEDIUM.value).count()
    low = db.query(Alert).filter(Alert.severity == AlertSeverity.LOW.value).count()
    
    new_alerts = db.query(Alert).filter(Alert.status == AlertStatus.NEW.value).count()
    investigating = db.query(Alert).filter(Alert.status == AlertStatus.INVESTIGATING.value).count()
    
    return {
        "total_alerts": total_alerts,
        "by_severity": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        },
        "by_status": {
            "new": new_alerts,
            "investigating": investigating
        }
    }
