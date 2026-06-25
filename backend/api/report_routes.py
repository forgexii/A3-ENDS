"""
Enhanced Reports Routes - With storage and download support
"""

from fastapi import APIRouter, Depends, HTTPException, Query, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.core.database import get_db
from backend.models.alert import Alert
from backend.models.detection import Detection
import os
import json
import uuid
from pathlib import Path

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

# Store for tracking report generation status
_report_status = {}
REPORTS_DIR = Path.home() / "Desktop" / "A3-ENDS_Reports"


@router.post("/generate")
def generate_report(
    payload: dict,
    db: Session = Depends(get_db)
):
    """Start report generation"""
    
    report_type = payload.get("report_type", "word")
    incident_id = payload.get("incident_id")
    
    # Generate unique report ID
    report_id = str(uuid.uuid4())[:8]
    
    # Track generation status
    _report_status[report_id] = {
        "status": "PROCESSING",
        "progress": 10,
        "report_type": report_type,
        "created_at": datetime.utcnow().isoformat(),
        "file_path": None
    }
    
    # Create reports directory if not exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Get data for report
        alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(100).all()
        detections = db.query(Detection).all()
        
        # Generate report
        alert_data = [
            {
                "id": a.id,
                "timestamp": a.timestamp.isoformat(),
                "severity": a.severity,
                "attack_type": a.attack_type,
                "source_ip": a.source_ip,
                "destination_ip": a.destination_ip,
                "risk_score": float(a.risk_score),
                "status": a.status,
            }
            for a in alerts
        ]
        
        # Map report type to file extension
        ext_map = {
            "Forensic Report": "pdf",
            "Executive Report": "pdf",
            "Incident Report": "pdf",
            "Word Document": "docx",
            "Excel Workbook": "xlsx",
            "PowerPoint Deck": "pptx",
        }
        
        file_ext = ext_map.get(report_type, "pdf")
        filename = f"Report_{report_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
        file_path = REPORTS_DIR / filename
        
        # Generate actual report (mock for now)
        _generate_report_file(file_path, report_type, alert_data)
        
        # Update status
        _report_status[report_id] = {
            "status": "COMPLETE",
            "progress": 100,
            "report_type": report_type,
            "created_at": datetime.utcnow().isoformat(),
            "file_path": str(file_path),
            "filename": filename
        }
        
        return {
            "report_id": report_id,
            "status": "PROCESSING",
            "message": "Report generation started"
        }
    
    except Exception as e:
        _report_status[report_id] = {
            "status": "FAILED",
            "error": str(e),
            "progress": 0
        }
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/status")
def get_report_status(report_id: str):
    """Get report generation status"""
    
    if report_id not in _report_status:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return _report_status[report_id]


@router.get("/{report_id}/download")
def download_report(report_id: str):
    """Download generated report"""
    
    if report_id not in _report_status:
        raise HTTPException(status_code=404, detail="Report not found")
    
    status = _report_status[report_id]
    
    if status["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Report not ready")
    
    file_path = Path(status["file_path"])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        path=file_path,
        filename=status["filename"],
        media_type="application/octet-stream"
    )


@router.get("/history")
def get_report_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get report generation history"""
    
    # Sort by creation time (newest first)
    history = sorted(
        _report_status.items(),
        key=lambda x: x[1].get("created_at", ""),
        reverse=True
    )
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated = history[start:end]
    
    reports = [
        {
            "report_id": report_id,
            "status": data.get("status"),
            "report_type": data.get("report_type"),
            "created_at": data.get("created_at"),
            "file_path": data.get("file_path"),
            "filename": data.get("filename"),
        }
        for report_id, data in paginated
    ]
    
    return {
        "reports": reports,
        "total": len(_report_status),
        "page": page,
        "page_size": page_size
    }


@router.get("/summary")
def get_reports_summary(db: Session = Depends(get_db)):
    """Get report generation summary"""
    
    completed = sum(1 for s in _report_status.values() if s.get("status") == "COMPLETE")
    failed = sum(1 for s in _report_status.values() if s.get("status") == "FAILED")
    total_size = sum(
        os.path.getsize(s.get("file_path")) 
        for s in _report_status.values() 
        if s.get("file_path") and os.path.exists(s.get("file_path"))
    )
    
    return {
        "total_generated": len(_report_status),
        "completed": completed,
        "failed": failed,
        "total_storage_used": total_size,
        "storage_location": str(REPORTS_DIR),
        "reports_directory": str(REPORTS_DIR)
    }


def _generate_report_file(file_path: Path, report_type: str, alert_data: list):
    """Generate actual report file (mock implementation)"""
    
    # For now, create a simple JSON file as placeholder
    # In production, use reportlab, python-docx, openpyxl, python-pptx
    
    content = {
        "report_type": report_type,
        "generated_at": datetime.utcnow().isoformat(),
        "alerts_included": len(alert_data),
        "alerts": alert_data[:20],  # Limit to first 20 for file size
    }
    
    # Create appropriate file type
    if file_path.suffix == ".json":
        with open(file_path, "w") as f:
            json.dump(content, f, indent=2)
    else:
        # For other formats, create placeholder JSON (production would use proper libraries)
        with open(str(file_path).replace(file_path.suffix, ".json"), "w") as f:
            json.dump(content, f, indent=2)
    
    file_path.touch()