from fastapi import APIRouter
from api.v1.health import router as health_router
from api.v1.auth import router as auth_router
from api.v1.evaluations import router as evaluations_router
from api.v1.exploration import router as exploration_router
from api.v1.tasks import router as tasks_router
from api.v1.scanning import router as scanning_router
from api.v1.sampling import router as sampling_router
from api.v1.findings import router as findings_router
from api.v1.wcag import router as wcag_router
from api.v1.reports import router as reports_router
from api.v1.audit import router as audit_router
from api.v1.organisations import router as organisations_router
from api.v1.invitations import router as invitations_router

# Master router — all routes live under /api/v1
# Add new routers here as you build them
api_router = APIRouter(prefix="/api/v1")

# ── Registered routes ──────────────────────────────
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(evaluations_router, prefix="/evaluations")

# Exploration routes nested under evaluations
api_router.include_router(exploration_router, prefix="/evaluations")

# Sampling routes nested under evaluations
api_router.include_router(sampling_router, prefix="/evaluations")

# Scanning routes nested under evaluations
api_router.include_router(scanning_router, prefix="/evaluations")

# Findings routes - evaluation-scoped endpoints
api_router.include_router(findings_router, prefix="/evaluations")

# Findings routes - single finding endpoints (need separate prefix)
api_router.include_router(findings_router, prefix="")

# Reports routes - evaluation-scoped endpoints
api_router.include_router(reports_router, prefix="/evaluations")

# Audit log routes - evaluation-scoped endpoints
api_router.include_router(audit_router, prefix="/evaluations")

# WCAG criteria routes
api_router.include_router(wcag_router, prefix="/wcag")

# Task status routes
api_router.include_router(tasks_router, prefix="/tasks")

# Organisation management routes
api_router.include_router(organisations_router, prefix="/organisations")

# Invitation routes (includes both /organisations/{id}/invitations and /invitations)
api_router.include_router(invitations_router, prefix="")
