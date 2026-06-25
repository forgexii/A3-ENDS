"""
Settings Routes - Frontend Integration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.schemas.dashboard_schema import (
    SettingsResponse,
    SettingsUpdateRequest,
)

router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)

# In-memory settings (in production, store in database)
_settings = {
    "detection_threshold": 0.73,
    "anomaly_detection_threshold": 0.75,
    "detection_window": 500,
    "risk_score_threshold": 75,
    "adwin_delta": 0.002,
    "adwin_clock": 32,
    "model_version": "3.2",
    "auto_refresh_interval": 5,
    "theme": "dark",
    "enable_notifications": True,
    "enable_auto_response": False,
}


@router.get("/", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db)
):
    """Get all settings"""
    return SettingsResponse(
        detection_threshold=_settings["detection_threshold"],
        anomaly_detection_threshold=_settings["anomaly_detection_threshold"],
        detection_window=_settings["detection_window"],
        risk_score_threshold=_settings["risk_score_threshold"],
        adwin_delta=_settings["adwin_delta"],
        adwin_clock=_settings["adwin_clock"],
        model_version=_settings["model_version"],
        auto_refresh_interval=_settings["auto_refresh_interval"],
    )


@router.put("/")
def update_settings(
    request: SettingsUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update settings"""
    if request.detection_threshold is not None:
        _settings["detection_threshold"] = request.detection_threshold
    
    if request.anomaly_detection_threshold is not None:
        _settings["anomaly_detection_threshold"] = request.anomaly_detection_threshold
    
    if request.detection_window is not None:
        _settings["detection_window"] = request.detection_window
    
    if request.risk_score_threshold is not None:
        _settings["risk_score_threshold"] = request.risk_score_threshold
    
    if request.adwin_delta is not None:
        _settings["adwin_delta"] = request.adwin_delta
    
    if request.adwin_clock is not None:
        _settings["adwin_clock"] = request.adwin_clock
    
    if request.auto_refresh_interval is not None:
        _settings["auto_refresh_interval"] = request.auto_refresh_interval
    
    return {
        "status": "success",
        "message": "Settings updated"
    }


@router.get("/detection")
def get_detection_settings():
    """Get detection-specific settings"""
    return {
        "anomaly_threshold": _settings["anomaly_detection_threshold"],
        "detection_window": _settings["detection_window"],
        "risk_score_threshold": _settings["risk_score_threshold"],
        "confidence_threshold": 0.70,
    }


@router.get("/ai-models")
def get_ai_model_settings():
    """Get AI model settings"""
    return {
        "adwin_delta": _settings["adwin_delta"],
        "adwin_clock": _settings["adwin_clock"],
        "model_version": _settings["model_version"],
        "lightgbm_confidence_threshold": 0.65,
        "autoencoder_threshold": _settings["detection_threshold"],
        "ensemble_method": "weighted_voting",
    }


@router.get("/database")
def get_database_settings():
    """Get database settings"""
    return {
        "database_type": "sqlite",
        "connection_string": "sqlite:///./a3ends.db",
        "backup_enabled": True,
        "backup_interval_hours": 24,
        "retention_days": 90,
        "max_query_timeout_seconds": 30,
    }


@router.get("/display")
def get_display_settings():
    """Get display settings"""
    return {
        "theme": _settings["theme"],
        "auto_refresh_interval": _settings["auto_refresh_interval"],
        "alert_table_row_limit": 200,
        "chart_animation_enabled": True,
        "dark_mode": True,
        "font_size": 12,
    }


@router.put("/detection")
def update_detection_settings(
    request: dict,
    db: Session = Depends(get_db)
):
    """Update detection settings"""
    if "anomaly_threshold" in request:
        _settings["anomaly_detection_threshold"] = request["anomaly_threshold"]
    
    if "detection_window" in request:
        _settings["detection_window"] = request["detection_window"]
    
    if "risk_score_threshold" in request:
        _settings["risk_score_threshold"] = request["risk_score_threshold"]
    
    return {"status": "success", "message": "Detection settings updated"}


@router.put("/ai-models")
def update_ai_model_settings(
    request: dict,
    db: Session = Depends(get_db)
):
    """Update AI model settings"""
    if "adwin_delta" in request:
        _settings["adwin_delta"] = request["adwin_delta"]
    
    if "adwin_clock" in request:
        _settings["adwin_clock"] = request["adwin_clock"]
    
    return {"status": "success", "message": "AI model settings updated"}


@router.post("/reset-defaults")
def reset_to_defaults(
    db: Session = Depends(get_db)
):
    """Reset all settings to defaults"""
    global _settings
    _settings = {
        "detection_threshold": 0.73,
        "anomaly_detection_threshold": 0.75,
        "detection_window": 500,
        "risk_score_threshold": 75,
        "adwin_delta": 0.002,
        "adwin_clock": 32,
        "model_version": "3.2",
        "auto_refresh_interval": 5,
        "theme": "dark",
        "enable_notifications": True,
        "enable_auto_response": False,
    }
    
    return {"status": "success", "message": "Settings reset to defaults"}
