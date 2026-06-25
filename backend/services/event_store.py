"""
Event Store

Stores realtime detection
events into SQLite.
"""

from backend.core.database import (
    SessionLocal
)

from backend.models.detection import (
    Detection
)


class EventStore:

    def __init__(self):

        self.db = SessionLocal()

    def add_event(
        self,
        event: dict
    ):

        detection = Detection(
            **event
        )

        self.db.add(
            detection
        )

        self.db.commit()

        self.db.refresh(
            detection
        )

        return detection

    def get_events(self):

        return self.db.query(
            Detection
        ).all()

    def close(self):

        self.db.close()