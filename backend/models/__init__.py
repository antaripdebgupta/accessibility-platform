"""
SQLAlchemy ORM Models Package.

This module imports all models to ensure they are registered with SQLAlchemy's
metadata for Alembic autogenerate support.
"""

from models.organisation import Organisation
from models.user import User
from models.user_org_role import UserOrganisationRole
from models.invitation import Invitation
from models.wcag import WcagCriterion
from models.evaluation import EvaluationProject
from models.page import Page
from models.finding import Finding
from models.report import Report
from models.audit_log import AuditLog

__all__ = [
    "Organisation",
    "User",
    "UserOrganisationRole",
    "Invitation",
    "WcagCriterion",
    "EvaluationProject",
    "Page",
    "Finding",
    "Report",
    "AuditLog",
]
