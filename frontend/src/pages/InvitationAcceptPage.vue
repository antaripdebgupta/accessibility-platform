<template>
  <div
    class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8"
  >
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <!-- Logo -->
      <div class="flex justify-center">
        <div class="flex items-center gap-2">
          <div
            class="h-10 w-10 rounded-lg bg-primary-600 flex items-center justify-center"
          >
            <span class="text-white font-bold text-lg">A</span>
          </div>
          <span class="text-xl font-semibold text-gray-900">A11y Platform</span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="mt-8 text-center">
        <div
          class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"
        ></div>
        <p class="mt-4 text-sm text-gray-500">Loading invitation...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="mt-8">
        <BaseCard class="text-center">
          <XCircleIcon class="mx-auto h-12 w-12 text-red-500" />
          <h2 class="mt-4 text-xl font-semibold text-gray-900">
            Invalid Invitation
          </h2>
          <p class="mt-2 text-sm text-gray-600">{{ error }}</p>
          <div class="mt-6">
            <BaseButton
              variant="primary"
              @click="router.push({ name: 'SignIn' })"
            >
              Go to Sign In
            </BaseButton>
          </div>
        </BaseCard>
      </div>

      <!-- Invitation Details -->
      <div v-else-if="invitation" class="mt-8">
        <BaseCard class="text-center">
          <EnvelopeOpenIcon class="mx-auto h-12 w-12 text-primary-500" />
          <h2 class="mt-4 text-xl font-semibold text-gray-900">
            You've Been Invited
          </h2>
          <p class="mt-2 text-sm text-gray-600">You've been invited to join</p>
          <p class="mt-1 text-lg font-semibold text-gray-900">
            {{ invitation.organisation_name }}
          </p>
          <p class="mt-2 text-sm text-gray-500">
            as a
            <span
              class="font-medium"
              :class="getRoleBadgeClass(invitation.role)"
              >{{ invitation.role }}</span
            >
          </p>

          <!-- Already Accepted -->
          <div v-if="invitation.status === 'accepted'" class="mt-6">
            <CheckCircleIcon class="mx-auto h-8 w-8 text-green-500" />
            <p class="mt-2 text-sm text-gray-600">
              This invitation has already been accepted.
            </p>
            <div class="mt-4">
              <BaseButton variant="primary" @click="goToDashboard">
                Go to Dashboard
              </BaseButton>
            </div>
          </div>

          <!-- Expired -->
          <div
            v-else-if="invitation.status === 'expired' || isExpired"
            class="mt-6"
          >
            <ClockIcon class="mx-auto h-8 w-8 text-gray-400" />
            <p class="mt-2 text-sm text-gray-600">
              This invitation has expired. Please contact the organisation owner
              for a new invitation.
            </p>
          </div>

          <!-- Revoked -->
          <div v-else-if="invitation.status === 'revoked'" class="mt-6">
            <XCircleIcon class="mx-auto h-8 w-8 text-gray-400" />
            <p class="mt-2 text-sm text-gray-600">
              This invitation has been revoked.
            </p>
          </div>

          <!-- Pending - Show Accept Button -->
          <div v-else class="mt-6 space-y-4">
            <!-- Not logged in -->
            <div v-if="!authStore.user">
              <p class="text-sm text-gray-600 mb-4">
                Please sign in to accept this invitation.
              </p>
              <BaseButton variant="primary" @click="signInAndAccept">
                Sign In to Accept
              </BaseButton>
            </div>

            <!-- Logged in as different email -->
            <div
              v-else-if="authStore.user.email !== invitation.email"
              class="space-y-4"
            >
              <div class="rounded-md bg-yellow-50 p-4 text-left">
                <div class="flex">
                  <ExclamationTriangleIcon
                    class="h-5 w-5 text-yellow-400 shrink-0"
                  />
                  <div class="ml-3">
                    <p class="text-sm text-yellow-700">
                      This invitation was sent to
                      <strong>{{ invitation.email }}</strong
                      >, but you're signed in as
                      <strong>{{ authStore.user.email }}</strong
                      >.
                    </p>
                  </div>
                </div>
              </div>
              <div class="flex gap-3 justify-center">
                <BaseButton variant="secondary" @click="signOut">
                  Sign Out
                </BaseButton>
                <BaseButton variant="primary" @click="signInAndAccept">
                  Sign In with Correct Account
                </BaseButton>
              </div>
            </div>

            <!-- Logged in with correct email - Accept -->
            <div v-else>
              <p class="text-sm text-gray-600 mb-4">
                Signed in as <strong>{{ authStore.user.email }}</strong>
              </p>
              <div class="flex gap-3 justify-center">
                <BaseButton
                  variant="secondary"
                  @click="router.push({ name: 'Dashboard' })"
                >
                  Decline
                </BaseButton>
                <BaseButton
                  variant="primary"
                  @click="acceptInvitation"
                  :loading="accepting"
                >
                  Accept Invitation
                </BaseButton>
              </div>
            </div>
          </div>

          <!-- Expiry Notice -->
          <p
            v-if="invitation.status === 'pending' && !isExpired"
            class="mt-6 text-xs text-gray-400"
          >
            This invitation expires on {{ formatDate(invitation.expires_at) }}
          </p>
        </BaseCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  CheckCircleIcon,
  ClockIcon,
  EnvelopeOpenIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'
import BaseCard from '../components/BaseCard.vue'
import api from '../lib/api'
import { useAuthStore } from '../stores/auth'
import { useOrgStore } from '../stores/org'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const orgStore = useOrgStore()

const token = computed(() => route.params.token)

const loading = ref(true)
const error = ref('')
const invitation = ref(null)
const accepting = ref(false)

const isExpired = computed(() => {
  if (!invitation.value?.expires_at) return false
  return new Date(invitation.value.expires_at) < new Date()
})

function getRoleBadgeClass(role) {
  const classes = {
    owner: 'text-purple-700',
    auditor: 'text-blue-700',
    reviewer: 'text-green-700',
    viewer: 'text-gray-700',
  }
  return classes[role] || 'text-gray-700'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function fetchInvitation() {
  loading.value = true
  error.value = ''

  try {
    const response = await api.get(`/invitations/${token.value}`)
    invitation.value = response.data
  } catch (err) {
    console.error('Failed to fetch invitation:', err)
    if (err.response?.status === 404) {
      error.value = 'This invitation link is invalid or has been removed.'
    } else if (err.response?.data?.detail) {
      error.value = err.response.data.detail
    } else {
      error.value = 'Failed to load invitation. Please try again.'
    }
  } finally {
    loading.value = false
  }
}

function signInAndAccept() {
  // Redirect to sign in with a return URL
  const returnUrl = route.fullPath
  router.push({
    name: 'SignIn',
    query: { redirect: returnUrl },
  })
}

async function signOut() {
  await authStore.logout()
  // Stay on the same page after sign out
}

async function acceptInvitation() {
  accepting.value = true

  try {
    await api.post(`/invitations/${token.value}/accept`)

    // Refresh the user's organisations
    await orgStore.fetchMyOrgs()

    // Find the newly joined organisation
    const newOrg = orgStore.organisations.find(
      (o) => o.id === invitation.value.organisation_id,
    )

    if (newOrg) {
      // Switch to the new organisation
      await orgStore.switchOrg(newOrg.id)
    }

    // Redirect to dashboard
    router.push({ name: 'Dashboard' })
  } catch (err) {
    console.error('Failed to accept invitation:', err)
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail
    } else {
      error.value = 'Failed to accept invitation. Please try again.'
    }
  } finally {
    accepting.value = false
  }
}

function goToDashboard() {
  router.push({ name: 'Dashboard' })
}

onMounted(async () => {
  await fetchInvitation()
})
</script>
