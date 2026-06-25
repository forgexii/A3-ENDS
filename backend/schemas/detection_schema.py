"""
Detection Schemas
"""

from datetime import datetime

from pydantic import BaseModel


class DetectionResponse(

    BaseModel

):

    id: int

    timestamp: datetime

    source_ip: str

    destination_ip: str

    source_port: int

    destination_port: int

    protocol: int

    anomaly_score: float

    threshold: float

    is_anomaly: bool

    classification: int | None = None

    attack_type: str | None = None

    confidence: float | None = None

    severity: str | None = None

    risk_score: float | None = None

    class Config:

        from_attributes = True