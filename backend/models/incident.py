"""
Incident Model
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Float
from datetime import datetime
from backend.core.database import Base
import enum


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    attack_type = Column(String, nullable=False, index=True)
    source_ip = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    status = Column(String, default=IncidentStatus.NEW, nullable=False, index=True)
    assigned_to = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Forensic analysis data
    forensic_analysis = Column(Text, nullable=True)  # JSON string
    
    # Timeline events
    timeline_data = Column(Text, nullable=True)  # JSON string
    
    # Related IPs
    affected_ips = Column(Text, nullable=True)  # JSON array string
    
    # Statistics
    alert_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    class Config:
        from_attributes = True
