"""
Dashboard Schemas for Frontend
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class DashboardKPI(BaseModel):
    """KPI metric card"""
    title: str
    value: int
    subtitle: str
    trend: Optional[float] = None  # Percentage trend
    severity: Optional[str] = None  # critical, warning, success, info


class RecentAlert(BaseModel):
    """Recent alert for dashboard"""
    id: str
    time: str
    source_ip: str
    attack_type: str
    severity: str
    status: str


class ActivityEvent(BaseModel):
    """Activity feed event"""
    timestamp: str
    severity: str
    message: str
    event_type: str


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics"""
    total_flows: int
    active_connections: int
    total_alerts: int
    critical_incidents: int
    detection_rate: float


class DashboardResponse(BaseModel):
    """Complete dashboard data"""
    kpis: List[DashboardKPI]
    recent_alerts: List[RecentAlert]
    activity_feed: List[ActivityEvent]
    attack_distribution: Dict[str, int]
    detection_trend: List[Dict[str, Any]]
    system_status: Dict[str, str]
    last_updated: str


class SettingsResponse(BaseModel):
    """System settings"""
    detection_threshold: float
    anomaly_detection_threshold: float
    detection_window: int
    risk_score_threshold: int
    adwin_delta: float
    adwin_clock: int
    model_version: str
    auto_refresh_interval: int


class SettingsUpdateRequest(BaseModel):
    """Update settings"""
    detection_threshold: Optional[float] = None
    anomaly_detection_threshold: Optional[float] = None
    detection_window: Optional[int] = None
    risk_score_threshold: Optional[int] = None
    adwin_delta: Optional[float] = None
    adwin_clock: Optional[int] = None
    auto_refresh_interval: Optional[int] = None
