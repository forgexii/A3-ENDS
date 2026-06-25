"""
Alert Model
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum
from datetime import datetime
from backend.core.database import Base
import enum


class AlertSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AlertStatus(str, enum.Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source_ip = Column(String, nullable=False, index=True)
    destination_ip = Column(String, nullable=False, index=True)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String, nullable=False)
    attack_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)  # 0-99
    confidence = Column(Float, nullable=False)  # 0-99
    status = Column(String, default=AlertStatus.NEW, nullable=False, index=True)
    
    # Anomaly detection
    anomaly_score = Column(Float, nullable=True)
    
    # Classification
    classification_confidence = Column(Float, nullable=True)
    
    # Explainability
    shap_explanation = Column(Text, nullable=True)  # JSON string
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    class Config:
        from_attributes = True
