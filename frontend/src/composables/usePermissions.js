/**
 * usePermissions Composable
 *
 * Provides convenient permission checking for Vue components.
 * Wraps the org store's permission system with common helpers.
 *
 * @example
 * import { usePermissions } from '@/composables/usePermissions'
 *
 * const { can, canEdit, canDelete, isOwner, isAuditor, isReviewer, isViewer } = usePermissions()
 *
 * // Check specific permission
 * if (can('evaluation.create')) { ... }
 *
 * // Use in templates
 * <button v-if="can('evaluation.delete')">Delete</button>
 */

import { computed } from 'vue'
import { useOrgStore } from '../stores/org'

export function usePermissions() {
  const orgStore = useOrgStore()

  /**
   * Check if the user can perform a specific action.
   * @param {string} action - The permission action to check
   * @returns {boolean} Whether the user has permission
   */
  function can(action) {
    return orgStore.can(action)
  }

  // Role-based computed properties
  const currentRole = computed(() => orgStore.currentRole)
  const isOwner = computed(() => orgStore.isOwner)
  const isAuditor = computed(() => orgStore.isAuditor)
  const isReviewer = computed(() => orgStore.isReviewer)
  const isViewer = computed(() => orgStore.currentRole === 'viewer')

  // Permission-based helpers for common actions
  const canCreateEvaluation = computed(() => can('evaluation.create'))
  const canEditEvaluation = computed(() => can('evaluation.update'))
  const canDeleteEvaluation = computed(() => can('evaluation.delete'))
  const canAdvanceEvaluation = computed(() => can('evaluation.advance'))

  const canStartExploration = computed(() => can('exploration.start'))
  const canStartScan = computed(() => can('scan.start'))

  const canCreateManualFinding = computed(() => can('finding.create_manual'))
  const canConfirmFinding = computed(() => can('finding.confirm'))
  const canDismissFinding = computed(() => can('finding.dismiss'))
  const canReopenFinding = computed(() => can('finding.reopen'))

  const canGenerateReport = computed(() => can('report.generate'))

  const canManageMembers = computed(() => can('org.manage_members'))
  const canInviteMembers = computed(() => can('org.invite'))
  const canViewAuditLog = computed(() => can('audit_log.read'))

  return {
    // Core function
    can,

    // Role checks
    currentRole,
    isOwner,
    isAuditor,
    isReviewer,
    isViewer,

    // Evaluation permissions
    canCreateEvaluation,
    canEditEvaluation,
    canDeleteEvaluation,
    canAdvanceEvaluation,

    // Exploration & Scan permissions
    canStartExploration,
    canStartScan,

    // Finding permissions
    canCreateManualFinding,
    canConfirmFinding,
    canDismissFinding,
    canReopenFinding,

    // Report permissions
    canGenerateReport,

    // Org management permissions
    canManageMembers,
    canInviteMembers,
    canViewAuditLog,
  }
}
