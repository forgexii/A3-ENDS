"""
System Health Schemas for Frontend
"""

from pydantic import BaseModel
from typing import List, Optional


class SystemMetricGauge(BaseModel):
    """Gauge metric (CPU, Memory, etc.)"""
    name: str  # CPU, Memory, Disk I/O, Network
    value: float  # Percentage 0-100
    unit: str = "%"
    status: str  # healthy, warning, critical


class ComponentHealth(BaseModel):
    """Individual component health"""
    component_name: str
    status: str  # online, offline, warning
    uptime_percent: float
    throughput: Optional[str] = None  # e.g., "4.2 Gbps"
    latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
    metadata: Optional[dict] = None


class SystemHealthResponse(BaseModel):
    """Complete system health"""
    gauges: List[SystemMetricGauge]
    components: List[ComponentHealth]
    overall_status: str  # healthy, degraded, critical
    last_updated: str
    timestamp: str


class ComponentHealthDetail(BaseModel):
    """Detailed component status"""
    component: ComponentHealth
    metrics: List[dict]  # Additional metrics
    alerts: List[str]  # Any alerts for this component
    recommendations: List[str]  # Recommendations if issues
