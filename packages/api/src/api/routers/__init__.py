"""CodeWarden API Routers."""

from api.routers.events import router as events_router
from api.routers.projects import router as projects_router
from api.routers.telemetry import router as telemetry_router
from api.routers.dashboard import router as dashboard_router
from api.routers.security import router as security_router
from api.routers.webhooks import router as webhooks_router

__all__ = [
    "events_router",
    "projects_router",
    "telemetry_router",
    "dashboard_router",
    "security_router",
    "webhooks_router",
]
