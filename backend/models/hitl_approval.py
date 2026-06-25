"""
HITL Approval Model

Persists pending analyst approvals to SQLite so that:
- State is shared between the realtime runner and the FastAPI process
- Timeouts survive process restarts
- The backend is the single source of truth for countdown state
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from datetime import datetime
from backend.core.database import Base


class HITLApproval(Base):
    __tablename__ = "hitl_approvals"

    id = Column(String, primary_key=True, index=True)          # detection_id / pipeline_id
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    timeout_seconds = Column(Integer, nullable=False, default=300)
    severity = Column(String, nullable=False)
    attack_type = Column(String, nullable=True)
    source_ip = Column(String, nullable=True)
    dest_ip = Column(String, nullable=True)
    source_port = Column(Integer, nullable=True)
    dest_port = Column(Integer, nullable=True)
    protocol = Column(String, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    shap_explanation = Column(Text, nullable=True)   # JSON string
    response_actions = Column(Text, nullable=True)   # JSON array string
    auto_execute = Column(Boolean, default=False)
    status = Column(String, default="pending", nullable=False, index=True)  # pending | approved | rejected | investigated | timeout
    analyst_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    class Config:
        from_attributes = True
