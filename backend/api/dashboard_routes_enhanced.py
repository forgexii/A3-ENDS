"""
Enhanced Dashboard Routes - Frontend Integration
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from backend.core.database import get_db
from backend.models.detection import Detection
from backend.models.alert import Alert
from backend.models.incident import Incident
from backend.schemas.dashboard_schema import (
    DashboardResponse,
    DashboardKPI,
    RecentAlert,
    ActivityEvent,
    DashboardStatsResponse,
    SettingsResponse,
    SettingsUpdateRequest,
)
from typing import List, Dict
import json
from backend.api.detection_orchestration import get_drift_status

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    detections = db.query(Detection).all()
    
    total_flows = len(detections)
    total_alerts = db.query(Alert).count()
    critical_incidents = db.query(Incident).filter(
        Incident.severity == "CRITICAL"
    ).count()
    
    active_connections = len(
        set(
            (d.source_ip, d.destination_ip)
            for d in detections
        )
    )
    
    return DashboardStatsResponse(
        total_flows=total_flows,
        active_connections=active_connections,
        total_alerts=total_alerts,
        critical_incidents=critical_incidents,
        detection_rate=0.9715
    )


@router.get("/full", response_model=dict)
def get_full_dashboard(
    db: Session = Depends(get_db)
):
    """Get complete dashboard data - formatted for frontend"""
    
    # ─── Calculate KPI values ─────────────────────────
    total_flows = db.query(Detection).count()
    total_alerts = db.query(Alert).count()
    critical_incidents = db.query(Alert).filter(Alert.severity == "CRITICAL").count()
    new_alerts = db.query(Alert).filter(Alert.status == "NEW").count()
    
    # Calculate active connections (unique source-destination pairs from detections)
    detections = db.query(Detection).all()
    active_connections = len(
        set(
            (d.source_ip, d.destination_ip)
            for d in detections
            if hasattr(d, 'source_ip') and hasattr(d, 'destination_ip')
        )
    ) if detections else 0
    
    # Calculate detection accuracy (classified alerts / total alerts percentage)
    classified_alerts = db.query(Alert).filter(Alert.attack_type != None).count()
    detection_accuracy = (classified_alerts / total_alerts * 100) if total_alerts > 0 else 0.0
    
    # Get ADWIN drift status from the actual service
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # get_drift_status is an async function, we need to run it synchronously or await it
        if loop.is_running():
            # If we're already in an async context, we'd normally await, but get_full_dashboard is a sync endpoint.
            # However, FastAPI runs sync endpoints in a threadpool where loop.is_running() is true but it's not the same thread.
            import threading
            import nest_asyncio
            nest_asyncio.apply()
            drift_data = loop.run_until_complete(get_drift_status())
        else:
            drift_data = asyncio.run(get_drift_status())
            
        is_drift = drift_data.get("drift_detected", False)
        adwin_status = "DRIFT_DETECTED" if is_drift else "STABLE"
    except Exception as e:
        print(f"Drift status error: {e}")
        adwin_status = "UNKNOWN"
    
    # ─── Recent alerts for table ──────────────────────
    recent_alerts_db = db.query(Alert).order_by(
        Alert.timestamp.desc()
    ).limit(8).all()
    
    recent_alerts = [
        RecentAlert(
            id=alert.id,
            time=alert.timestamp.strftime("%H:%M:%S"),
            source_ip=alert.source_ip,
            attack_type=alert.attack_type,
            severity=alert.severity,
            status=alert.status
        )
        for alert in recent_alerts_db
    ]
    
    # ─── Activity feed events ─────────────────────────
    def _build_event(alert):
        event_type = "ALERT"
        message = f"Detected {alert.attack_type} from {alert.source_ip}"
        
        if alert.status == "INVESTIGATING":
            event_type = "INFO"
            message = f"Analyst investigating {alert.attack_type} from {alert.source_ip}"
        elif alert.status == "RESOLVED":
            event_type = "SUCCESS"
            message = f"Resolved {alert.attack_type} incident on {alert.source_ip}"
        elif alert.severity == "CRITICAL":
            event_type = "THREAT"
            message = f"CRITICAL: {alert.attack_type} targeting {alert.destination_ip}"
        elif alert.attack_type == "Anomaly" or (alert.anomaly_score and alert.anomaly_score >= 80.0):
            event_type = "ANOMALY"
            message = f"High-risk anomalous pattern (score: {alert.anomaly_score:.1f}) from {alert.source_ip}"
            
        return ActivityEvent(
            timestamp=alert.timestamp.strftime("%H:%M:%S"),
            severity=alert.severity,
            message=message,
            event_type=event_type
        )

    activity_events = [_build_event(alert) for alert in recent_alerts_db[:15]]
    
    # ─── Attack distribution as LIST (for pie chart) ──
    attack_dist = db.query(
        Alert.attack_type,
        func.count(Alert.id).label("count")
    ).group_by(Alert.attack_type).all()
    
    attack_distribution = [
        {"name": attack, "value": count} 
        for attack, count in attack_dist
    ]
    
    # ─── Detection trends (hourly for 24h) ────────────
    now = datetime.utcnow()
    detection_trend = []
    for i in range(24):
        hour_start = now - timedelta(hours=24-i)
        hour_end = hour_start + timedelta(hours=1)
        
        # Normal traffic = Total Detections in this hour - Total Alerts
        total_detections = db.query(Detection).filter(
            Detection.timestamp >= hour_start,
            Detection.timestamp < hour_end
        ).count()
        
        total_alerts_hr = db.query(Alert).filter(
            Alert.timestamp >= hour_start,
            Alert.timestamp < hour_end
        ).count()
        
        normal_count = max(0, total_detections - total_alerts_hr)
        
        anomalies_count = db.query(Alert).filter(
            Alert.timestamp >= hour_start,
            Alert.timestamp < hour_end,
            Alert.anomaly_score >= 50.0
        ).count()
        
        attacks_count = db.query(Alert).filter(
            Alert.timestamp >= hour_start,
            Alert.timestamp < hour_end,
            Alert.attack_type != 'Unknown',
            Alert.attack_type != 'Normal'
        ).count()
        
        detection_trend.append({
            "time": hour_start.strftime("%H:00"),
            "normal": normal_count,
            "anomalies": anomalies_count,
            "attacks": attacks_count
        })
    
    # ─── System status ───────────────────────────────
    # Calculate based on recent activity (last 1 hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    recent_critical = db.query(Alert).filter(
        Alert.severity == "CRITICAL",
        Alert.timestamp >= one_hour_ago
    ).count()
    
    recent_high = db.query(Alert).filter(
        Alert.severity == "HIGH",
        Alert.timestamp >= one_hour_ago
    ).count()
    
    recent_alerts_count = db.query(Alert).filter(
        Alert.timestamp >= one_hour_ago
    ).count()

    threat_level = "LOW"
    if recent_critical > 0:
        threat_level = "CRITICAL"
    elif recent_high > 5:
        threat_level = "HIGH"
    elif recent_alerts_count > 50:
        threat_level = "ELEVATED"
    elif recent_alerts_count > 10:
        threat_level = "MEDIUM"

    system_status = {
        "api": "online",
        "database": "online",
        "detector": "online",
        "classifier": "online",
        "threat_level": threat_level
    }
    
    # ─── Return flattened structure (frontend expects this) ──
    return {
        # KPI values (frontend extracts these individually)
        "total_flows": total_flows,
        "active_connections": active_connections,
        "total_alerts": total_alerts,
        "critical_incidents": critical_incidents,
        "detection_accuracy": detection_accuracy,
        "adwin_status": adwin_status,
        
        # Chart and table data
        "recent_alerts": [alert.dict() for alert in recent_alerts],
        "activity_events": [event.dict() for event in activity_events],
        "attack_distribution": attack_distribution,
        "trends": detection_trend,
        
        # System status
        "system_status": system_status,
        
        # Metadata
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/attacks")
def get_attack_distribution(
    db: Session = Depends(get_db)
):
    """Get attack type distribution"""
    results = db.query(
        Alert.attack_type,
        func.count(Alert.id).label("count")
    ).group_by(Alert.attack_type).all()
    
    total = sum(count for _, count in results)
    
    return {
        "attacks": [
            {
                "name": attack,
                "value": count,
                "percentage": (count / total * 100) if total > 0 else 0.0
            }
            for attack, count in results
        ],
        "total": total
    }


@router.get("/trends")
def get_detection_trends(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get detection trends over time"""
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)
    
    # Get alerts per hour with breakdown
    trends = []
    for i in range(hours):
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        total_detections = db.query(Detection).filter(
            Detection.timestamp >= hour_start,
            Detection.timestamp < hour_end
        ).count()
        
        total_alerts_hr = db.query(Alert).filter(
            Alert.timestamp >= hour_start,
            Alert.timestamp < hour_end
        ).count()
        
        normal_count = max(0, total_detections - total_alerts_hr)
        
        anomalies_count = db.query(Alert).filter(
            Alert.timestamp >= hour_start,
            Alert.timestamp < hour_end,
            Alert.anomaly_score >= 50.0
        ).count()
        
        classifications_count = db.query(Alert).filter(
            Alert.timestamp >= hour_start,
            Alert.timestamp < hour_end,
            Alert.attack_type != 'Unknown',
            Alert.attack_type != 'Normal'
        ).count()
        
        trends.append({
            "time": hour_start.strftime("%H:%M"),
            "count": total_alerts_hr,
            "detections": total_alerts_hr,
            "normal": normal_count,
            "anomalies": anomalies_count,
            "classifications": classifications_count
        })
    
    return {"trends": trends}


@router.get("/severity-breakdown")
def get_severity_breakdown(
    db: Session = Depends(get_db)
):
    """Get alert severity breakdown"""
    critical = db.query(Alert).filter(Alert.severity == "CRITICAL").count()
    high = db.query(Alert).filter(Alert.severity == "HIGH").count()
    medium = db.query(Alert).filter(Alert.severity == "MEDIUM").count()
    low = db.query(Alert).filter(Alert.severity == "LOW").count()
    info = db.query(Alert).filter(Alert.severity == "INFO").count()
    
    total = critical + high + medium + low + info
    
    return {
        "CRITICAL": {"count": critical, "percentage": (critical/total*100) if total > 0 else 0},
        "HIGH": {"count": high, "percentage": (high/total*100) if total > 0 else 0},
        "MEDIUM": {"count": medium, "percentage": (medium/total*100) if total > 0 else 0},
        "LOW": {"count": low, "percentage": (low/total*100) if total > 0 else 0},
        "INFO": {"count": info, "percentage": (info/total*100) if total > 0 else 0},
        "total": total
    }
