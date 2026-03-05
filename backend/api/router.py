from fastapi import APIRouter
from api.v1.health import router as health_router
from api.v1.auth import router as auth_router
from api.v1.evaluations import router as evaluations_router
from api.v1.exploration import router as exploration_router
from api.v1.tasks import router as tasks_router

# Master router — all routes live under /api/v1
# Add new routers here as you build them
api_router = APIRouter(prefix="/api/v1")

# ── Registered routes ──────────────────────────
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(evaluations_router, prefix="/evaluations")

# Exploration routes nested under evaluations
api_router.include_router(exploration_router, prefix="/evaluations")

# Task status routes
api_router.include_router(tasks_router, prefix="/tasks")
