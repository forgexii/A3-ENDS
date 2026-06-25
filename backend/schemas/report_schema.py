"""
Report Schemas for Frontend
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ReportHistoryItem(BaseModel):
    """Report history item"""
    report_id: str
    report_type: str  # forensic, executive, incident, word, excel, pptx
    generated_at: datetime
    status: str  # PENDING, COMPLETE, FAILED
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None


class ReportGenerationRequest(BaseModel):
    """Request to generate a report"""
    report_type: str  # forensic, executive, incident, word, excel, pptx
    incident_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    include_recommendations: Optional[bool] = True


class ReportGenerationResponse(BaseModel):
    """Response from report generation"""
    status: str  # PENDING, COMPLETE, FAILED
    report_id: str
    report_type: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    generated_at: Optional[datetime] = None
    message: Optional[str] = None


class ReportListResponse(BaseModel):
    """List of reports"""
    reports: List[ReportHistoryItem]
    total: int
    page: int
    page_size: int
