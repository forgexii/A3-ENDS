"""
Enhanced Reports Routes - Frontend Integration

Supports three forensic report formats:
  - docx  — Word narrative report
  - pptx  — PowerPoint executive briefing
  - xlsx  — Excel incident data spreadsheet

Also supports:
  - json  — Raw LLM analysis as JSON
  - html  — Forensic and executive HTML summaries (existing stubs kept)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import os
import json

from backend.core.database import get_db
from backend.core.paths import REPORTS_DIR
from backend.models.alert import Alert
from backend.models.incident import Incident
from backend.schemas.report_schema import (
    ReportGenerationRequest,
    ReportGenerationResponse,
    ReportListResponse,
    ReportHistoryItem,
)

router = APIRouter(prefix="/reports", tags=["Reports"])

# In-memory report tracking (keyed by report_id)
_report_history: dict = {}

# Ensure the reports directory exists
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# BACKGROUND: generate the actual file
# ---------------------------------------------------------------------------

def _generate_report_file(
    report_id: str,
    report_type: str,
    report_data: dict,
):
    """
    Run in a FastAPI BackgroundTask.
    Dispatches to the appropriate builder and updates _report_history.
    """
    from backend.reports.html_generator import generate_html_report
    from backend.llm.report_generator import generate_llm_report

    try:
        # Fetch LLM analysis (may return an error dict — handle gracefully)
        llm_result = generate_llm_report(report_data)
        if isinstance(llm_result, str):
            report_data["llm_analysis"] = llm_result
        else:
            report_data["llm_analysis"] = json.dumps(llm_result, indent=2)

        # We now generate PDF for all report requests
        ext = "pdf"
        output_path = REPORTS_DIR / f"report_{report_id}.{ext}"
        
        generate_html_report(report_data, output_path)

        _report_history[report_id].update({
            "status":       "COMPLETE",
            "file_path":    str(output_path),
            "file_size":    output_path.stat().st_size,
            "download_url": f"/api/reports/download/{report_id}",
        })

    except Exception as exc:
        _report_history[report_id]["status"]  = "FAILED"
        _report_history[report_id]["message"] = str(exc)
        print(f"[ReportGen] Failed for {report_id}: {exc}")


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=ReportGenerationResponse)
def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Request report generation (docx / pptx / xlsx / json)."""

    report_id   = str(uuid.uuid4())[:8]
    report_type = request.report_type.lower()

    # Gather context data from DB
    report_data: dict = {
        "report_id":   report_id,
        "report_type": report_type,
        "timestamp":   datetime.utcnow().isoformat(),
    }

    if request.incident_id:
        incident = db.query(Incident).filter(Incident.id == request.incident_id).first()
        if incident:
            report_data.update({
                "detection_id":    incident.id,
                "attack_type":     incident.attack_type,
                "severity":        incident.severity,
                "source_ip":       incident.source_ip,
                "analyst_decision": incident.status,
                "analyst_notes":   incident.notes,
            })
            # Pull most recent associated alert for ML fields
            alert = (
                db.query(Alert)
                .filter(Alert.source_ip == incident.source_ip)
                .order_by(Alert.timestamp.desc())
                .first()
            )
            if alert:
                shap = None
                if alert.shap_explanation:
                    try:
                        shap = json.loads(alert.shap_explanation)
                    except Exception:
                        pass
                report_data.update({
                    "dest_ip":          alert.destination_ip,
                    "source_port":      alert.source_port,
                    "dest_port":        alert.destination_port,
                    "protocol":         alert.protocol,
                    "risk_score":       alert.risk_score,
                    "confidence":       alert.confidence,
                    "anomaly_score":    alert.anomaly_score,
                    "shap_explanation": shap,
                })
    else:
        # Use the most recent alert
        alert = db.query(Alert).order_by(Alert.timestamp.desc()).first()
        if alert:
            shap = None
            if alert.shap_explanation:
                try:
                    shap = json.loads(alert.shap_explanation)
                except Exception:
                    pass
            report_data.update({
                "detection_id":    alert.id,
                "attack_type":     alert.attack_type,
                "severity":        alert.severity,
                "source_ip":       alert.source_ip,
                "dest_ip":         alert.destination_ip,
                "source_port":     alert.source_port,
                "dest_port":       alert.destination_port,
                "protocol":        alert.protocol,
                "risk_score":      alert.risk_score,
                "confidence":      alert.confidence,
                "anomaly_score":   alert.anomaly_score,
                "shap_explanation": shap,
            })

    # Register as pending
    _report_history[report_id] = {
        "report_id":   report_id,
        "report_type": "pdf",
        "status":      "PENDING",
        "generated_at": datetime.utcnow(),
        "message":     "Report generation started",
    }

    background_tasks.add_task(_generate_report_file, report_id, report_type, report_data)

    return ReportGenerationResponse(
        status="PENDING",
        report_id=report_id,
        report_type=report_type,
        generated_at=datetime.utcnow(),
        message=f"Generating {report_type.upper()} report...",
    )


@router.get("/history", response_model=ReportListResponse)
def get_report_history(page: int = 1, page_size: int = 25, db: Session = Depends(get_db)):
    reports = sorted(_report_history.values(), key=lambda x: x["generated_at"], reverse=True)
    total   = len(reports)
    start   = (page - 1) * page_size
    items   = [
        ReportHistoryItem(
            report_id    = r["report_id"],
            report_type  = r["report_type"],
            generated_at = r["generated_at"],
            status       = r["status"],
            file_path    = r.get("file_path"),
            file_size    = r.get("file_size"),
            download_url = r.get("download_url"),
        )
        for r in reports[start: start + page_size]
    ]
    return ReportListResponse(reports=items, total=total, page=page, page_size=page_size)


@router.get("/status/{report_id}")
def get_report_status(report_id: str):
    if report_id not in _report_history:
        raise HTTPException(status_code=404, detail="Report not found")
    r = _report_history[report_id]
    return ReportGenerationResponse(
        status       = r["status"],
        report_id    = report_id,
        report_type  = r["report_type"],
        file_path    = r.get("file_path"),
        generated_at = r.get("generated_at"),
        download_url = r.get("download_url"),
        message      = r.get("message"),
    )


@router.get("/download/{report_id}")
def download_report(report_id: str):
    """Stream the generated report file."""
    if report_id not in _report_history:
        raise HTTPException(status_code=404, detail="Report not found")

    r = _report_history[report_id]
    if r["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail=f"Report is {r['status']}")

    file_path = r.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    ext_to_media = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "pdf": "application/pdf",
    }
    ext        = file_path.rsplit(".", 1)[-1].lower()
    media_type = ext_to_media.get(ext, "application/octet-stream")

    return FileResponse(
        path            = file_path,
        media_type      = media_type,
        filename        = f"A3-ENDS_report_{report_id}.{ext}",
    )


@router.get("/summary")
def get_reports_summary():
    """Storage summary for the UI."""
    total_size = sum(
        r.get("file_size", 0) for r in _report_history.values()
        if r.get("file_size")
    )
    return {
        "reports_directory": str(REPORTS_DIR),
        "total_reports":     len(_report_history),
        "total_size_bytes":  total_size,
        "by_type": {
            fmt: sum(1 for r in _report_history.values() if r["report_type"] == fmt)
            for fmt in ("docx", "pptx", "xlsx", "json")
        },
    }


@router.delete("/delete/{report_id}")
def delete_report(report_id: str):
    if report_id not in _report_history:
        raise HTTPException(status_code=404, detail="Report not found")
    r = _report_history.pop(report_id)
    fp = r.get("file_path")
    if fp and os.path.exists(fp):
        os.remove(fp)
    return {"status": "success", "message": "Report deleted"}


# ---------------------------------------------------------------------------
# Legacy forensic / executive stubs (kept for backward compat)
# ---------------------------------------------------------------------------

@router.post("/forensic")
def generate_forensic_report(incident_id: str = None, db: Session = Depends(get_db)):
    """Shorthand: generate a DOCX forensic report for an incident."""
    from fastapi import BackgroundTasks
    req  = ReportGenerationRequest(report_type="docx", incident_id=incident_id)
    bt   = BackgroundTasks()
    return generate_report(req, bt, db)


@router.post("/executive")
def generate_executive_report(db: Session = Depends(get_db)):
    """Shorthand: generate a PPTX executive briefing."""
    from fastapi import BackgroundTasks
    req = ReportGenerationRequest(report_type="pptx")
    bt  = BackgroundTasks()
    return generate_report(req, bt, db)
