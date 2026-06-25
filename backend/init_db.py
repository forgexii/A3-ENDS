"""
Initialize Database
"""

from backend.core.database import (
    Base,
    engine,
    SessionLocal
)

from backend.models.detection import (
    Detection
)

from backend.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus
)

from backend.models.incident import (
    Incident
)

from datetime import datetime, timedelta
import random
import uuid


def init_db():
    """Initialize database and create seed data."""
    
    Base.metadata.create_all(bind=engine)
    
    # Create seed data if tables are empty
    db = SessionLocal()
    
    # Check if alerts already exist
    existing_alerts = db.query(Alert).count()
    if existing_alerts == 0:
        print("Creating seed data...")
        
        # Sample attack types and severities
        attack_types = ["DDoS", "Port Scan", "Brute Force", "SQL Injection", "Lateral Movement"]
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        statuses = ["NEW", "INVESTIGATING", "ESCALATED", "RESOLVED", "FALSE_POSITIVE"]
        protocols = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS"]
        
        # Create sample alerts for the last 24 hours
        now = datetime.utcnow()
        for i in range(50):
            alert = Alert(
                id=str(uuid.uuid4()),
                timestamp=now - timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59)),
                source_ip=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                destination_ip=f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}",
                source_port=random.randint(1024, 65535),
                destination_port=random.choice([22, 80, 443, 3306, 5432, 8000, 8080]),
                protocol=random.choice(protocols),
                attack_type=random.choice(attack_types),
                severity=random.choice(severities),
                risk_score=random.uniform(10, 99),
                confidence=random.uniform(50, 99),
                status=random.choice(statuses),
                anomaly_score=random.uniform(0, 1),
                classification_confidence=random.uniform(50, 99),
            )
            db.add(alert)
        
        db.commit()
        print(f"Created 50 seed alerts")
    
    db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized with seed data.")