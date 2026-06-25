from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio

# Import all routers
from backend.api.detection_routes import (
    router as detection_router
)

from backend.api.detection_orchestration import (
    router as detection_orchestration_router,
    _enforce_hitl_timeouts,
)

from backend.api.dashboard_routes_enhanced import (
    router as dashboard_router_enhanced
)

from backend.api.alerts_routes import (
    router as alerts_router
)

from backend.api.incidents_routes import (
    router as incidents_router
)

from backend.api.system_health_routes import (
    router as system_health_router
)

from backend.api.reports_routes_enhanced import (
    router as reports_router_enhanced
)

from backend.api.websocket_routes import (
    router as websocket_router
)

# Ensure all DB tables exist (including hitl_approvals)
from backend.core.database import engine, Base
import backend.models.alert          # noqa: F401
import backend.models.detection      # noqa: F401
import backend.models.incident       # noqa: F401
import backend.models.hitl_approval  # noqa: F401
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="A3-ENDS API",
    description="AI-Powered Network Intrusion Detection System Backend",
    version="2.3.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(detection_router,               prefix="/api")
app.include_router(detection_orchestration_router, prefix="/api")
app.include_router(dashboard_router_enhanced,      prefix="/api")
app.include_router(alerts_router,                  prefix="/api")
app.include_router(incidents_router,               prefix="/api")
app.include_router(system_health_router,           prefix="/api")
app.include_router(reports_router_enhanced,        prefix="/api")
app.include_router(websocket_router,               prefix="/api")


# ---------------------------------------------------------------------------
# HITL TIMEOUT SCHEDULER
# Runs every 10 seconds in the background to enforce server-side timeouts.
# This is independent of any UI-side countdown timer.
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def start_hitl_scheduler():
    """Launch the HITL timeout-enforcement loop on startup."""
    asyncio.create_task(_hitl_timeout_loop())


async def _hitl_timeout_loop():
    """Async background task: enforce pending HITL timeouts every 10 s."""
    while True:
        await asyncio.sleep(10)
        try:
            await asyncio.get_event_loop().run_in_executor(None, _enforce_hitl_timeouts)
        except Exception as exc:
            print(f"[HITL-Scheduler] Error: {exc}")


# ---------------------------------------------------------------------------
# HEALTH / VERSION
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status":    "online",
        "platform":  "A3-ENDS",
        "version":   "2.3.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/health")
def health_check():
    return {
        "status":    "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api":           "online",
            "database":      "online",
            "detection":     "online",
            "classification": "online",
            "orchestration": "online",
            "hitl_scheduler": "online",
        },
    }


@app.get("/api/version")
def get_version():
    return {
        "version":      "2.3.0",
        "build":        "20260623",
        "platform":     "A3-ENDS",
        "backend_name": "FastAPI",
    }