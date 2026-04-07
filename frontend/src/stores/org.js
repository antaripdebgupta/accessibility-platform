/**
 * Organisation Pinia Store
 *
 * Manages state for multi-tenancy including:
 * - List of organisations the user belongs to
 * - Current active organisation
 * - Organisation members and invitations
 * - Organisation switching with localStorage persistence
 * - User role and permissions for RBAC
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../lib/api'

const LOCAL_STORAGE_KEY = 'current_org_id'

/**
 * Permission definitions mapped by role.
 * This mirrors the backend permissions.py for client-side checks.
 */
const ROLE_PERMISSIONS = {
  owner: [
    'evaluation.create',
    'evaluation.read',
    'evaluation.update',
    'evaluation.delete',
    'evaluation.advance',
    'exploration.start',
    'exploration.read',
    'scan.start',
    'finding.read',
    'finding.create_manual',
    'finding.confirm',
    'finding.dismiss',
    'finding.reopen',
    'report.generate',
    'report.read',
    'org.view_members',
    'org.manage_members',
    'org.invite',
    'audit_log.read',
  ],
  auditor: [
    'evaluation.create',
    'evaluation.read',
    'evaluation.update',
    'evaluation.advance',
    'exploration.start',
    'exploration.read',
    'scan.start',
    'finding.read',
    'finding.create_manual',
    'finding.confirm',
    'finding.dismiss',
    'finding.reopen',
    'report.generate',
    'report.read',
    'org.view_members',
    'audit_log.read',
  ],
  reviewer: [
    'evaluation.read',
    'exploration.read',
    'finding.read',
    'finding.confirm',
    'finding.dismiss',
    'report.read',
    'org.view_members',
  ],
  viewer: [
    'evaluation.read',
    'exploration.read',
    'finding.read',
    'report.read',
    'org.view_members',
  ],
}

export const useOrgStore = defineStore('org', () => {
  // State
  const organisations = ref([])
  const current = ref(null)
  const members = ref([])
  const invitations = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const hasOrganisations = computed(() => organisations.value.length > 0)
  const currentRole = computed(() => {
    if (!current.value) return null
    const org = organisations.value.find((o) => o.id === current.value.id)
    return org?.role || null
  })
  const isOwner = computed(() => currentRole.value === 'owner')
  const isAuditor = computed(
    () => currentRole.value === 'owner' || currentRole.value === 'auditor',
  )
  const isReviewer = computed(
    () =>
      currentRole.value === 'owner' ||
      currentRole.value === 'auditor' ||
      currentRole.value === 'reviewer',
  )
  const currentOrgId = computed(() => current.value?.id || null)
  const ownerCount = computed(() => {
    return members.value.filter((m) => m.role === 'owner').length
  })

  /**
   * Get the permissions for the current role.
   * @returns {string[]} Array of permission strings
   */
  const permissions = computed(() => {
    if (!currentRole.value) return []
    return ROLE_PERMISSIONS[currentRole.value] || []
  })

  /**
   * Check if the user can perform a specific action.
   * @param {string} action - The permission action to check
   * @returns {boolean} Whether the user has permission
   */
  function can(action) {
    return permissions.value.includes(action)
  }

  /**
   * Fetch all organisations the current user belongs to.
   * Restores current org from localStorage if available.
   */
  async function fetchMyOrgs() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/organisations/me')
      organisations.value = response.data || []

      // Restore current org from localStorage
      const savedOrgId = localStorage.getItem(LOCAL_STORAGE_KEY)

      if (savedOrgId) {
        const savedOrg = organisations.value.find((o) => o.id === savedOrgId)
        if (savedOrg) {
          current.value = savedOrg
        } else if (organisations.value.length > 0) {
          // Saved org not in list, default to first
          current.value = organisations.value[0]
          localStorage.setItem(LOCAL_STORAGE_KEY, current.value.id)
        }
      } else if (organisations.value.length > 0) {
        // No saved org, default to first
        current.value = organisations.value[0]
        localStorage.setItem(LOCAL_STORAGE_KEY, current.value.id)
      }

      return organisations.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch organisations'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Switch to a different organisation.
   * Persists to localStorage and refreshes evaluations.
   * @param {string} orgId - Organisation UUID to switch to
   */
  async function switchOrg(orgId) {
    const org = organisations.value.find((o) => o.id === orgId)
    if (!org) {
      throw new Error('Organisation not found')
    }

    current.value = org
    localStorage.setItem(LOCAL_STORAGE_KEY, orgId)

    // Clear members and invitations from previous org
    members.value = []
    invitations.value = []

    // Refresh evaluations for new org
    // Import dynamically to avoid circular dependency
    const { useEvaluationsStore } = await import('./evaluations')
    const evaluationsStore = useEvaluationsStore()
    await evaluationsStore.fetchList()
  }

  /**
   * Create a new organisation.
   * @param {Object} data - Organisation data
   * @param {string} data.name - Organisation name
   * @param {string} data.slug - Organisation slug
   */
  async function createOrg(data) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/organisations', data)
      const newOrg = {
        ...response.data,
        role: 'owner', // Creator is always owner
      }

      organisations.value.push(newOrg)

      return newOrg
    } catch (err) {
      error.value = err.message || 'Failed to create organisation'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch members of an organisation.
   * @param {string} orgId - Organisation UUID
   */
  async function fetchMembers(orgId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/organisations/${orgId}/members`)
      members.value = response.data || []
      return members.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch members'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch invitations for an organisation.
   * @param {string} orgId - Organisation UUID
   */
  async function fetchInvitations(orgId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/organisations/${orgId}/invitations`)
      invitations.value = response.data || []
      return invitations.value
    } catch (err) {
      error.value = err.message || 'Failed to fetch invitations'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Send an invitation to join the organisation.
   * @param {string} orgId - Organisation UUID
   * @param {string} email - Email to invite
   * @param {string} role - Role to assign (auditor, reviewer, viewer)
   */
  async function sendInvitation(orgId, email, role) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/organisations/${orgId}/invitations`, {
        email,
        role,
      })
      const invitation = response.data

      // Add to invitations list
      invitations.value.unshift(invitation)

      return invitation
    } catch (err) {
      error.value = err.message || 'Failed to send invitation'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Revoke a pending invitation.
   * @param {string} orgId - Organisation UUID
   * @param {string} invitationId - Invitation UUID
   */
  async function revokeInvitation(orgId, invitationId) {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/organisations/${orgId}/invitations/${invitationId}`)

      // Update status in local list
      const idx = invitations.value.findIndex((i) => i.id === invitationId)
      if (idx !== -1) {
        invitations.value[idx].status = 'revoked'
      }
    } catch (err) {
      error.value = err.message || 'Failed to revoke invitation'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update a member's role in the organisation.
   * @param {string} orgId - Organisation UUID
   * @param {string} userId - User UUID
   * @param {string} role - New role
   */
  async function updateMemberRole(orgId, userId, role) {
    loading.value = true
    error.value = null

    try {
      const response = await api.patch(
        `/organisations/${orgId}/members/${userId}`,
        { role },
      )

      // Update in local list
      const idx = members.value.findIndex((m) => m.user_id === userId)
      if (idx !== -1) {
        members.value[idx] = response.data
      }

      return response.data
    } catch (err) {
      error.value = err.message || 'Failed to update member role'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Remove a member from the organisation.
   * @param {string} orgId - Organisation UUID
   * @param {string} userId - User UUID
   */
  async function removeMember(orgId, userId) {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/organisations/${orgId}/members/${userId}`)

      // Remove from local list
      members.value = members.value.filter((m) => m.user_id !== userId)
    } catch (err) {
      error.value = err.message || 'Failed to remove member'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear organisation state (on logout).
   */
  function clear() {
    organisations.value = []
    current.value = null
    members.value = []
    invitations.value = []
    error.value = null
  }

  return {
    // State
    organisations,
    current,
    members,
    invitations,
    loading,
    error,

    // Computed
    hasOrganisations,
    currentRole,
    isOwner,
    isAuditor,
    isReviewer,
    currentOrgId,
    ownerCount,
    permissions,

    // Actions
    can,
    fetchMyOrgs,
    switchOrg,
    createOrg,
    fetchMembers,
    fetchInvitations,
    sendInvitation,
    revokeInvitation,
    updateMemberRole,
    removeMember,
    clear,
  }
})
