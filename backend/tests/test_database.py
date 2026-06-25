from backend.core.database import (
    Base,
    engine
)

from backend.models.detection import (
    Detection
)


Base.metadata.create_all(
    bind=engine
)

print(
    "Database initialized."
)