"""
Permission matrix and role definitions for RBAC.

This module is the single source of truth for all role-based permissions
in the WCAG Accessibility Evaluation Platform.

Role Definitions:
- owner: Full control — manage org, members, delete anything
- auditor: Run crawls, run scans, create evaluations, confirm/dismiss findings
- reviewer: Review findings only — confirm/dismiss, add notes, cannot run scans
- viewer: Read-only — can view everything, change nothing
"""

from enum import Enum
from typing import List, Set


class Role(str, Enum):
    """User roles in the organisation."""

    OWNER = "owner"
    AUDITOR = "auditor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


# Every action in the system mapped to which roles can perform it
PERMISSIONS: dict[str, List[Role]] = {
    # Evaluation Permissions
    "evaluation.create": [Role.OWNER, Role.AUDITOR],
    "evaluation.read": [Role.OWNER, Role.AUDITOR, Role.REVIEWER, Role.VIEWER],
    "evaluation.update": [Role.OWNER, Role.AUDITOR],
    "evaluation.delete": [Role.OWNER],
    "evaluation.advance": [Role.OWNER, Role.AUDITOR],

    # Exploration Permissions
    "exploration.start": [Role.OWNER, Role.AUDITOR],
    "exploration.read": [Role.OWNER, Role.AUDITOR, Role.REVIEWER, Role.VIEWER],

    # Scanning Permissions
    "scan.start": [Role.OWNER, Role.AUDITOR],

    # Finding Permissions
    "finding.read": [Role.OWNER, Role.AUDITOR, Role.REVIEWER, Role.VIEWER],
    "finding.create_manual": [Role.OWNER, Role.AUDITOR],
    "finding.confirm": [Role.OWNER, Role.AUDITOR, Role.REVIEWER],
    "finding.dismiss": [Role.OWNER, Role.AUDITOR, Role.REVIEWER],
    "finding.reopen": [Role.OWNER, Role.AUDITOR, Role.REVIEWER],
    "finding.update": [Role.OWNER, Role.AUDITOR, Role.REVIEWER],

    # Report Permissions
    "report.generate": [Role.OWNER, Role.AUDITOR],
    "report.read": [Role.OWNER, Role.AUDITOR, Role.REVIEWER, Role.VIEWER],

    # Organisation Permissions
    "org.manage_members": [Role.OWNER],
    "org.invite": [Role.OWNER],
    "org.view_members": [Role.OWNER, Role.AUDITOR, Role.REVIEWER, Role.VIEWER],
    "org.delete": [Role.OWNER],

    # Audit Log Permissions
    "audit_log.read": [Role.OWNER, Role.AUDITOR],
}


def can(role: Role | str, action: str) -> bool:
    """
    Check if a role is allowed to perform a specific action.

    Args:
        role: The user's role (can be Role enum or string)
        action: The action string to check (e.g., "evaluation.create")

    Returns:
        True if the role is permitted to perform the action
    """
    # Convert string to Role enum if needed
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return False

    allowed = PERMISSIONS.get(action, [])
    return role in allowed


def get_permissions_for_role(role: Role | str) -> Set[str]:
    """
    Get all permission action strings for a given role.

    Args:
        role: The user's role (can be Role enum or string)

    Returns:
        Set of action strings the role can perform
    """
    # Convert string to Role enum if needed
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return set()

    return {action for action, roles in PERMISSIONS.items() if role in roles}


def get_all_roles() -> List[str]:
    """
    Get all valid role strings.

    Returns:
        List of role value strings
    """
    return [r.value for r in Role]
