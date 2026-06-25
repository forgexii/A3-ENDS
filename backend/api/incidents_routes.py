"""
Incidents Routes - Frontend Integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from backend.core.database import get_db
from backend.models.incident import Incident, IncidentStatus
from backend.models.alert import Alert
from backend.schemas.incident_schema import (
    IncidentResponse,
    IncidentListResponse,
    IncidentDetailResponse,
    IncidentUpdateRequest,
    TimelineEvent,
)
import json

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


@router.get("/", response_model=IncidentListResponse)
def get_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str = Query(None),
    severity: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated incidents with filtering"""
    query = db.query(Incident)
    
    if status:
        query = query.filter(Incident.status == status)
    
    if severity:
        query = query.filter(Incident.severity == severity)
    
    total = query.count()
    incidents = query.order_by(Incident.start_time.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    incident_responses = []
    for incident in incidents:
        # Calculate duration
        end_time = incident.end_time or datetime.utcnow()
        duration = int((end_time - incident.start_time).total_seconds())
        
        # Parse timeline
        timeline = []
        if incident.timeline_data:
            try:
                timeline_data = json.loads(incident.timeline_data)
                timeline = [
                    TimelineEvent(
                        timestamp=event.get("timestamp", ""),
                        severity=event.get("severity", "INFO"),
                        message=event.get("message", ""),
                        event_type=event.get("event_type", "")
                    )
                    for event in timeline_data
                ]
            except:
                pass
        
        # Parse affected IPs
        affected_ips = []
        if incident.affected_ips:
            try:
                affected_ips = json.loads(incident.affected_ips)
            except:
                pass
        
        incident_responses.append(
            IncidentResponse(
                id=incident.id,
                start_time=incident.start_time.strftime("%H:%M:%S"),
                attack_type=incident.attack_type,
                source=incident.source_ip,
                severity=incident.severity,
                timeline=timeline,
                status=incident.status,
                assigned_to=incident.assigned_to,
                notes=incident.notes,
                alert_count=incident.alert_count,
                duration_seconds=duration,
                affected_ips=affected_ips,
                detected_at=incident.start_time
            )
        )
    
    return IncidentListResponse(
        incidents=incident_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident_detail(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed incident information"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Calculate duration
    end_time = incident.end_time or datetime.utcnow()
    duration = int((end_time - incident.start_time).total_seconds())
    
    # Parse timeline
    timeline = []
    if incident.timeline_data:
        try:
            timeline_data = json.loads(incident.timeline_data)
            timeline = [
                TimelineEvent(
                    timestamp=event.get("timestamp", ""),
                    severity=event.get("severity", "INFO"),
                    message=event.get("message", ""),
                    event_type=event.get("event_type", "")
                )
                for event in timeline_data
            ]
        except:
            pass
    
    # Parse affected IPs
    affected_ips = []
    if incident.affected_ips:
        try:
            affected_ips = json.loads(incident.affected_ips)
        except:
            pass
    
    incident_response = IncidentResponse(
        id=incident.id,
        start_time=incident.start_time.strftime("%H:%M:%S"),
        attack_type=incident.attack_type,
        source=incident.source_ip,
        severity=incident.severity,
        timeline=timeline,
        status=incident.status,
        assigned_to=incident.assigned_to,
        notes=incident.notes,
        alert_count=incident.alert_count,
        duration_seconds=duration,
        affected_ips=affected_ips,
        detected_at=incident.start_time
    )
    
    # Get related alerts
    related_alerts = db.query(Alert).filter(
        (Alert.source_ip == incident.source_ip) |
        (Alert.destination_ip.in_(affected_ips))
    ).order_by(Alert.timestamp.desc()).limit(20).all()
    
    related_alerts_list = [
        {
            "id": alert.id,
            "timestamp": alert.timestamp.isoformat(),
            "source_ip": alert.source_ip,
            "destination_ip": alert.destination_ip,
            "attack_type": alert.attack_type,
            "severity": alert.severity,
        }
        for alert in related_alerts
    ]
    
    return IncidentDetailResponse(
        incident=incident_response,
        related_alerts=related_alerts_list,
        forensic_analysis=json.loads(incident.forensic_analysis) if incident.forensic_analysis else None,
        recommended_actions=[]
    )


@router.put("/{incident_id}")
def update_incident(
    incident_id: str,
    update_request: IncidentUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update incident status and assignment"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if update_request.status:
        incident.status = update_request.status
        if update_request.status == IncidentStatus.RESOLVED:
            incident.end_time = datetime.utcnow()
    
    if update_request.assigned_to:
        incident.assigned_to = update_request.assigned_to
    
    if update_request.notes:
        incident.notes = update_request.notes
    
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    return {"status": "success", "message": "Incident updated"}


@router.get("/stats/summary")
def get_incidents_summary(
    db: Session = Depends(get_db)
):
    """Get incident statistics summary"""
    total = db.query(Incident).count()
    critical = db.query(Incident).filter(Incident.severity == "CRITICAL").count()
    high = db.query(Incident).filter(Incident.severity == "HIGH").count()
    resolved = db.query(Incident).filter(Incident.status == IncidentStatus.RESOLVED).count()
    investigating = db.query(Incident).filter(Incident.status == IncidentStatus.INVESTIGATING).count()
    
    return {
        "total_incidents": total,
        "by_severity": {
            "critical": critical,
            "high": high
        },
        "by_status": {
            "resolved": resolved,
            "investigating": investigating
        }
    }
