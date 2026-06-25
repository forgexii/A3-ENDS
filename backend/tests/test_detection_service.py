from backend.core.database import (
    SessionLocal
)

from backend.services.detection_service import (
    detection_service
)

db = SessionLocal()

record = {

    "source_ip":
        "192.168.1.100",

    "destination_ip":
        "10.0.0.5",

    "source_port":
        54321,

    "destination_port":
        80,

    "protocol":
        6,

    "anomaly_score":
        0.91,

    "threshold":
        0.40,

    "is_anomaly":
        True,

    "classification":
        1,

    "attack_type":
        "PORTSCAN",

    "confidence":
        0.98,

    "severity":
        "HIGH",

    "risk_score":
        0.95
}

saved = (
    detection_service
    .create_detection(
        db,
        record
    )
)

print(saved.id)

print(

    detection_service
    .dashboard_stats(
        db
    )

)