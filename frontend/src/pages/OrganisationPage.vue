<template>
  <AppLayout>
    <PageHeader
      title="Organisation Settings"
      :back-to="{ name: 'Dashboard' }"
    />

    <!-- Tabs -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8" aria-label="Tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            activeTab === tab.id
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
            'whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors',
          ]"
        >
          <component :is="tab.icon" class="inline-block h-5 w-5 mr-2 -mt-0.5" />
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- Members Tab -->
    <div v-if="activeTab === 'members'">
      <div v-if="orgStore.loading" class="flex justify-center py-12">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"
        ></div>
      </div>

      <div v-else-if="orgStore.members.length === 0" class="text-center py-12">
        <UsersIcon class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">No members found</h3>
        <p class="mt-1 text-sm text-gray-500">
          This organisation has no members yet.
        </p>
      </div>

      <div
        v-else
        class="overflow-hidden rounded-lg border border-gray-200 bg-white"
      >
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Member
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Email
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Role
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Joined
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="member in orgStore.members" :key="member.user_id">
              <td class="whitespace-nowrap px-6 py-4">
                <div class="flex items-center">
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-full font-medium text-white"
                    :style="{
                      backgroundColor: getAvatarColor(
                        member.display_name || member.email,
                      ),
                    }"
                  >
                    {{ getInitials(member.display_name || member.email) }}
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">
                      {{ member.display_name || 'No name' }}
                    </div>
                  </div>
                </div>
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                {{ member.email }}
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-sm">
                <!-- Role dropdown for owners editing other members -->
                <template v-if="isOwner && !isCurrentUser(member.user_id)">
                  <div
                    class="relative"
                    :title="
                      isLastOwner(member) ? 'Cannot demote the last owner' : ''
                    "
                  >
                    <select
                      :value="member.role"
                      @change="
                        handleRoleChange(member.user_id, $event.target.value)
                      "
                      :disabled="isLastOwner(member)"
                      class="block w-full rounded-md border-gray-300 py-1.5 pl-3 pr-10 text-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    >
                      <option value="owner">Owner</option>
                      <option value="auditor">Auditor</option>
                      <option value="reviewer">Reviewer</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </div>
                </template>
                <!-- Read-only badge for non-owners or viewing self -->
                <template v-else>
                  <span
                    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                    :class="getRoleBadgeClass(member.role)"
                  >
                    {{ member.role }}
                  </span>
                </template>
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                {{ formatDate(member.joined_at) }}
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-right text-sm">
                <button
                  v-if="
                    isOwner &&
                    !isCurrentUser(member.user_id) &&
                    !isLastOwner(member)
                  "
                  @click="handleRemoveMember(member)"
                  class="text-red-600 hover:text-red-900 font-medium"
                >
                  Remove
                </button>
                <span
                  v-else-if="isCurrentUser(member.user_id)"
                  class="text-gray-400 text-xs"
                >
                  (You)
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Invitations Tab -->
    <div v-if="activeTab === 'invitations'">
      <!-- Invite Form (owners only) -->
      <div
        v-if="isOwner"
        class="mb-6 rounded-lg border border-gray-200 bg-white p-4"
      >
        <h3 class="text-sm font-medium text-gray-900 mb-4">Invite Member</h3>
        <form
          @submit.prevent="handleSendInvitation"
          class="flex flex-col sm:flex-row gap-3"
        >
          <div class="flex-1">
            <input
              v-model="inviteEmail"
              type="email"
              placeholder="Email address"
              required
              class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            />
          </div>
          <div class="sm:w-40">
            <select
              v-model="inviteRole"
              class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="auditor">Auditor</option>
              <option value="reviewer">Reviewer</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <BaseButton type="submit" variant="primary" :loading="sendingInvite">
            Send Invite
          </BaseButton>
        </form>
        <p v-if="inviteError" class="mt-2 text-sm text-red-600">
          {{ inviteError }}
        </p>
      </div>

      <div v-if="orgStore.loading" class="flex justify-center py-12">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"
        ></div>
      </div>

      <div
        v-else-if="orgStore.invitations.length === 0"
        class="text-center py-12"
      >
        <EnvelopeIcon class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">
          No invitations sent yet
        </h3>
        <p class="mt-1 text-sm text-gray-500">
          Invite team members to collaborate on evaluations.
        </p>
      </div>

      <div
        v-else
        class="overflow-hidden rounded-lg border border-gray-200 bg-white"
      >
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Email
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Role
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Invited By
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Expires
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Status
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="invitation in orgStore.invitations" :key="invitation.id">
              <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                {{ invitation.email }}
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-sm">
                <span
                  class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                  :class="getRoleBadgeClass(invitation.role)"
                >
                  {{ invitation.role }}
                </span>
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                {{ invitation.invited_by_email || 'Unknown' }}
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                {{ formatDate(invitation.expires_at) }}
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-sm">
                <span
                  class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                  :class="getStatusBadgeClass(invitation.status)"
                >
                  {{ invitation.status }}
                </span>
              </td>
              <td class="whitespace-nowrap px-6 py-4 text-right text-sm">
                <button
                  v-if="invitation.status === 'pending'"
                  @click="handleRevokeInvitation(invitation.id)"
                  class="text-red-600 hover:text-red-900 font-medium"
                >
                  Revoke
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Settings Tab -->
    <div v-if="activeTab === 'settings'">
      <div class="space-y-6">
        <!-- Organisation Name -->
        <div class="rounded-lg border border-gray-200 bg-white p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">
            Organisation Details
          </h3>

          <div class="space-y-4">
            <!-- Name -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1"
                >Organisation Name</label
              >
              <div v-if="!editingName" class="flex items-center">
                <span class="text-gray-900">{{ currentOrg?.name }}</span>
                <button
                  v-if="isOwner"
                  @click="startEditingName"
                  class="ml-3 text-sm text-primary-600 hover:text-primary-800"
                >
                  Edit
                </button>
              </div>
              <div v-else class="flex items-center gap-2">
                <input
                  v-model="editName"
                  type="text"
                  class="block w-full max-w-md rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
                <BaseButton
                  variant="primary"
                  size="sm"
                  @click="saveOrgName"
                  :loading="savingName"
                >
                  Save
                </BaseButton>
                <BaseButton
                  variant="secondary"
                  size="sm"
                  @click="cancelEditingName"
                >
                  Cancel
                </BaseButton>
              </div>
            </div>

            <!-- Slug (read-only) -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Slug
                <span class="text-gray-400 font-normal"
                  >(cannot be changed)</span
                >
              </label>
              <code
                class="inline-block bg-gray-100 px-3 py-1.5 rounded text-sm font-mono text-gray-700"
              >
                {{ currentOrg?.slug }}
              </code>
            </div>
          </div>
        </div>

        <!-- Danger Zone -->
        <div
          v-if="isOwner"
          class="rounded-lg border-2 border-red-200 bg-red-50 p-6"
        >
          <h3 class="text-lg font-medium text-red-900 mb-2">Danger Zone</h3>
          <p class="text-sm text-red-700 mb-4">
            Once you delete an organisation, there is no going back. All
            evaluations, findings, and reports will be permanently deleted.
          </p>
          <BaseButton variant="danger" @click="showDeleteModal = true">
            Delete Organisation
          </BaseButton>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <TransitionRoot appear :show="showDeleteModal" as="template">
      <Dialog as="div" @close="showDeleteModal = false" class="relative z-50">
        <TransitionChild
          as="template"
          enter="duration-300 ease-out"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="duration-200 ease-in"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black/25" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div
            class="flex min-h-full items-center justify-center p-4 text-center"
          >
            <TransitionChild
              as="template"
              enter="duration-300 ease-out"
              enter-from="opacity-0 scale-95"
              enter-to="opacity-100 scale-100"
              leave="duration-200 ease-in"
              leave-from="opacity-100 scale-100"
              leave-to="opacity-0 scale-95"
            >
              <DialogPanel
                class="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all"
              >
                <DialogTitle
                  as="h3"
                  class="text-lg font-medium leading-6 text-gray-900"
                >
                  Delete Organisation
                </DialogTitle>
                <div class="mt-4">
                  <p class="text-sm text-gray-500 mb-4">
                    This action cannot be undone. Type
                    <strong>{{ currentOrg?.name }}</strong> to confirm.
                  </p>
                  <input
                    v-model="deleteConfirmName"
                    type="text"
                    :placeholder="currentOrg?.name"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-sm"
                  />
                </div>

                <div class="mt-6 flex justify-end gap-3">
                  <BaseButton
                    variant="secondary"
                    @click="showDeleteModal = false"
                  >
                    Cancel
                  </BaseButton>
                  <BaseButton
                    variant="danger"
                    @click="handleDeleteOrganisation"
                    :disabled="deleteConfirmName !== currentOrg?.name"
                    :loading="deleting"
                  >
                    Delete Organisation
                  </BaseButton>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>

    <!-- Remove Member Confirmation Modal -->
    <TransitionRoot appear :show="showRemoveModal" as="template">
      <Dialog as="div" @close="showRemoveModal = false" class="relative z-50">
        <TransitionChild
          as="template"
          enter="duration-300 ease-out"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="duration-200 ease-in"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black/25" />
        </TransitionChild>

        <div class="fixed inset-0 overflow-y-auto">
          <div
            class="flex min-h-full items-center justify-center p-4 text-center"
          >
            <TransitionChild
              as="template"
              enter="duration-300 ease-out"
              enter-from="opacity-0 scale-95"
              enter-to="opacity-100 scale-100"
              leave="duration-200 ease-in"
              leave-from="opacity-100 scale-100"
              leave-to="opacity-0 scale-95"
            >
              <DialogPanel
                class="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all"
              >
                <DialogTitle
                  as="h3"
                  class="text-lg font-medium leading-6 text-gray-900"
                >
                  Remove Member
                </DialogTitle>
                <div class="mt-4">
                  <p class="text-sm text-gray-500">
                    Are you sure you want to remove
                    <strong>{{
                      memberToRemove?.display_name || memberToRemove?.email
                    }}</strong>
                    from this organisation?
                  </p>
                </div>

                <div class="mt-6 flex justify-end gap-3">
                  <BaseButton
                    variant="secondary"
                    @click="showRemoveModal = false"
                  >
                    Cancel
                  </BaseButton>
                  <BaseButton
                    variant="danger"
                    @click="confirmRemoveMember"
                    :loading="removing"
                  >
                    Remove
                  </BaseButton>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </TransitionRoot>
  </AppLayout>
</template>

<script setup>
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import {
  Cog6ToothIcon,
  EnvelopeIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import api from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { useOrgStore } from '../stores/org'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const orgStore = useOrgStore()

const orgId = computed(() => route.params.id)

const tabs = [
  { id: 'members', name: 'Members', icon: UsersIcon },
  { id: 'invitations', name: 'Invitations', icon: EnvelopeIcon },
  { id: 'settings', name: 'Settings', icon: Cog6ToothIcon },
]

const activeTab = ref('members')

// Members tab state
const showRemoveModal = ref(false)
const memberToRemove = ref(null)
const removing = ref(false)

// Invitations tab state
const inviteEmail = ref('')
const inviteRole = ref('auditor')
const sendingInvite = ref(false)
const inviteError = ref('')

// Settings tab state
const editingName = ref(false)
const editName = ref('')
const savingName = ref(false)
const showDeleteModal = ref(false)
const deleteConfirmName = ref('')
const deleting = ref(false)

const currentOrg = computed(() => {
  return orgStore.organisations.find((o) => o.id === orgId.value) || null
})

const isOwner = computed(() => {
  return currentOrg.value?.role === 'owner'
})

const ownerCount = computed(() => {
  return orgStore.members.filter((m) => m.role === 'owner').length
})

function isCurrentUser(userId) {
  return userId === authStore.userId
}

function isLastOwner(member) {
  return member.role === 'owner' && ownerCount.value <= 1
}

function getInitials(name) {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

function getAvatarColor(name) {
  if (!name) return '#6B7280'
  const colors = [
    '#EF4444',
    '#F97316',
    '#F59E0B',
    '#EAB308',
    '#84CC16',
    '#22C55E',
    '#10B981',
    '#14B8A6',
    '#06B6D4',
    '#0EA5E9',
    '#3B82F6',
    '#6366F1',
    '#8B5CF6',
    '#A855F7',
    '#D946EF',
    '#EC4899',
    '#F43F5E',
  ]
  const index = name.charCodeAt(0) % colors.length
  return colors[index]
}

function getRoleBadgeClass(role) {
  const classes = {
    owner: 'bg-purple-100 text-purple-700',
    auditor: 'bg-blue-100 text-blue-700',
    reviewer: 'bg-green-100 text-green-700',
    viewer: 'bg-gray-100 text-gray-700',
  }
  return classes[role] || 'bg-gray-100 text-gray-700'
}

function getStatusBadgeClass(status) {
  const classes = {
    pending: 'bg-blue-100 text-blue-700',
    accepted: 'bg-green-100 text-green-700',
    expired: 'bg-gray-100 text-gray-500',
    revoked: 'bg-gray-100 text-gray-500 line-through',
  }
  return classes[status] || 'bg-gray-100 text-gray-700'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

// Load data on mount
onMounted(async () => {
  if (orgId.value) {
    await Promise.all([
      orgStore.fetchMembers(orgId.value),
      orgStore.fetchInvitations(orgId.value),
    ])
  }
})

// Watch for tab changes to refetch data
watch(activeTab, async (newTab) => {
  if (newTab === 'members') {
    await orgStore.fetchMembers(orgId.value)
  } else if (newTab === 'invitations') {
    await orgStore.fetchInvitations(orgId.value)
  }
})

// Member management
async function handleRoleChange(userId, newRole) {
  try {
    await orgStore.updateMemberRole(orgId.value, userId, newRole)
  } catch (err) {
    console.error('Failed to update role:', err)
    alert(err.message || 'Failed to update role')
  }
}

function handleRemoveMember(member) {
  memberToRemove.value = member
  showRemoveModal.value = true
}

async function confirmRemoveMember() {
  if (!memberToRemove.value) return
  removing.value = true
  try {
    await orgStore.removeMember(orgId.value, memberToRemove.value.user_id)
    showRemoveModal.value = false
    memberToRemove.value = null
  } catch (err) {
    console.error('Failed to remove member:', err)
    alert(err.message || 'Failed to remove member')
  } finally {
    removing.value = false
  }
}

// Invitation management
async function handleSendInvitation() {
  if (!inviteEmail.value) return
  sendingInvite.value = true
  inviteError.value = ''

  try {
    await orgStore.sendInvitation(
      orgId.value,
      inviteEmail.value,
      inviteRole.value,
    )
    inviteEmail.value = ''
    inviteRole.value = 'auditor'
    // Show success toast (you could use a toast library here)
    alert(`Invitation sent to ${inviteEmail.value || 'the email address'}`)
  } catch (err) {
    inviteError.value = err.message || 'Failed to send invitation'
  } finally {
    sendingInvite.value = false
  }
}

async function handleRevokeInvitation(invitationId) {
  try {
    await orgStore.revokeInvitation(orgId.value, invitationId)
  } catch (err) {
    console.error('Failed to revoke invitation:', err)
    alert(err.message || 'Failed to revoke invitation')
  }
}

// Settings management
function startEditingName() {
  editName.value = currentOrg.value?.name || ''
  editingName.value = true
}

function cancelEditingName() {
  editingName.value = false
  editName.value = ''
}

async function saveOrgName() {
  if (!editName.value.trim()) return
  savingName.value = true

  try {
    await api.patch(`/organisations/${orgId.value}`, {
      name: editName.value.trim(),
    })
    // Update local state
    const org = orgStore.organisations.find((o) => o.id === orgId.value)
    if (org) {
      org.name = editName.value.trim()
    }
    if (orgStore.current?.id === orgId.value) {
      orgStore.current.name = editName.value.trim()
    }
    editingName.value = false
  } catch (err) {
    console.error('Failed to update name:', err)
    alert(err.message || 'Failed to update organisation name')
  } finally {
    savingName.value = false
  }
}

async function handleDeleteOrganisation() {
  if (deleteConfirmName.value !== currentOrg.value?.name) return
  deleting.value = true

  try {
    await api.delete(`/organisations/${orgId.value}`)
    // Remove from local state
    orgStore.organisations = orgStore.organisations.filter(
      (o) => o.id !== orgId.value,
    )
    // If this was the current org, switch to another
    if (orgStore.current?.id === orgId.value) {
      if (orgStore.organisations.length > 0) {
        await orgStore.switchOrg(orgStore.organisations[0].id)
      } else {
        orgStore.current = null
        localStorage.removeItem('current_org_id')
      }
    }
    router.push({ name: 'Dashboard' })
  } catch (err) {
    console.error('Failed to delete organisation:', err)
    alert(err.message || 'Failed to delete organisation')
  } finally {
    deleting.value = false
    showDeleteModal.value = false
  }
}
</script>
