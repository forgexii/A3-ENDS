"""
Incident Schemas for Frontend
"""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class TimelineEvent(BaseModel):
    """Timeline event for incident reconstruction"""
    timestamp: str  # HH:MM:SS format
    severity: str  # Color-coded: CRITICAL, HIGH, MEDIUM, LOW
    message: str  # Event description
    event_type: str  # Detection step type


class IncidentResponse(BaseModel):
    """Incident response model matching frontend expectations"""
    id: str  # INC-YYYYMMDD-XXXX format
    start_time: str  # HH:MM:SS
    attack_type: str
    source: str  # Source IP
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    timeline: List[TimelineEvent]
    status: str  # NEW, INVESTIGATING, ESCALATED, RESOLVED
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    alert_count: int = 0
    duration_seconds: int = 0
    affected_ips: List[str] = []
    detected_at: datetime = None

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    """List of incidents"""
    incidents: List[IncidentResponse]
    total: int
    page: int
    page_size: int


class IncidentDetailResponse(BaseModel):
    """Detailed incident information"""
    incident: IncidentResponse
    related_alerts: List[dict]
    forensic_analysis: Optional[dict] = None
    recommended_actions: List[str] = []


class IncidentUpdateRequest(BaseModel):
    """Update incident"""
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
