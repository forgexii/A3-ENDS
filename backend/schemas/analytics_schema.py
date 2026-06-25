"""
Analytics Schemas for Frontend
"""

from pydantic import BaseModel
from typing import List, Dict, Optional


class AnalyticsDataPoint(BaseModel):
    """Single data point for analytics"""
    timestamp: str
    value: float
    label: Optional[str] = None


class AnalyticsSeriesResponse(BaseModel):
    """Time series data for analytics charts"""
    series_name: str
    data: List[AnalyticsDataPoint]
    color: Optional[str] = None


class AttackDistributionResponse(BaseModel):
    """Attack type distribution"""
    attack_type: str
    count: int
    percentage: float
    severity: str


class DetectionMetricsResponse(BaseModel):
    """Detection performance metrics"""
    metric_name: str
    value: float
    trend: Optional[float] = None  # Positive or negative trend


class AnalyticsDashboardResponse(BaseModel):
    """Complete analytics data"""
    trends: List[AnalyticsSeriesResponse]
    attack_distribution: List[AttackDistributionResponse]
    performance_metrics: List[DetectionMetricsResponse]
    time_range: Dict[str, str]  # start, end
    total_detections: int
    anomalies_detected: int
    false_positives: int


class TimeWindowRequest(BaseModel):
    """Request analytics for time window"""
    start_time: str  # ISO format
    end_time: str  # ISO format
    metrics: Optional[List[str]] = None
