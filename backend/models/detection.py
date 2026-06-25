"""
Detection Model
"""

from sqlalchemy import (

    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime

)

from datetime import datetime

from backend.core.database import Base


class Detection(Base):

    __tablename__ = "detections"

    id = Column(

        Integer,

        primary_key=True,

        index=True

    )

    timestamp = Column(

        DateTime,

        default=datetime.utcnow,

        nullable=False

    )

    source_ip = Column(

        String,

        nullable=False

    )

    destination_ip = Column(

        String,

        nullable=False

    )

    source_port = Column(

        Integer,

        nullable=False

    )

    destination_port = Column(

        Integer,

        nullable=False

    )

    protocol = Column(

        Integer,

        nullable=False

    )

    anomaly_score = Column(

        Float,

        nullable=False

    )

    threshold = Column(

        Float,

        nullable=False

    )

    is_anomaly = Column(

        Boolean,

        nullable=False

    )

    classification = Column(

        Integer,

        nullable=True

    )

    attack_type = Column(

        String,

        nullable=True

    )

    confidence = Column(

        Float,

        nullable=True

    )

    severity = Column(

        String,

        nullable=True

    )

    risk_score = Column(

        Float,

        nullable=True

    )