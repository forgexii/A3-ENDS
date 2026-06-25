"""
Alert Schemas for Frontend
"""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class AlertResponse(BaseModel):
    """Alert response model matching frontend expectations"""
    id: str
    ts: str  # Time string (HH:MM:SS)
    src_ip: str
    dst_ip: str
    protocol: str
    attack: str  # Attack type
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    risk: int  # 0-99
    conf: int  # Confidence 0-99
    status: str  # NEW, INVESTIGATING, ESCALATED, RESOLVED, FALSE_POSITIVE
    timestamp: datetime  # Full timestamp for backend use
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    anomaly_score: Optional[float] = None
    classification_confidence: Optional[float] = None
    shap_explanation: Optional[dict] = None  # SHAP explainability data

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """List of alerts"""
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int


class AlertUpdateRequest(BaseModel):
    """Update alert status"""
    status: str
    notes: Optional[str] = None


class AlertDetailResponse(BaseModel):
    """Detailed alert information"""
    alert: AlertResponse
    timeline: List[dict]  # Related events
    indicators: List[str]  # IOCs (IPs, domains, etc.)
    mitre_tactics: List[str]  # MITRE ATT&CK tactics
