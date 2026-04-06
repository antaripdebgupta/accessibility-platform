<template>
  <AppLayout>
    <PageHeader title="Create Organisation" :back-to="{ name: 'Dashboard' }" />

    <div class="max-w-2xl">
      <BaseCard>
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <p class="text-sm text-gray-600">
            Create a new organisation to manage evaluations and collaborate with
            your team.
          </p>

          <!-- Organisation Name -->
          <div>
            <label
              for="name"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Organisation Name <span class="text-red-500">*</span>
            </label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              required
              placeholder="My Organisation"
              class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              @input="updateSlug"
            />
            <p class="mt-1 text-xs text-gray-500">
              This is the display name for your organisation.
            </p>
          </div>

          <!-- Organisation Slug -->
          <div>
            <label
              for="slug"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Slug <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center">
              <span
                class="inline-flex items-center rounded-l-md border border-r-0 border-gray-300 bg-gray-50 px-3 py-2 text-gray-500 sm:text-sm"
              >
                /orgs/
              </span>
              <input
                id="slug"
                v-model="form.slug"
                type="text"
                required
                pattern="[a-z0-9-]+"
                placeholder="my-organisation"
                class="block w-full rounded-none rounded-r-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm font-mono"
              />
            </div>
            <p class="mt-1 text-xs text-gray-500">
              A unique identifier for your organisation. Use lowercase letters,
              numbers, and hyphens only. This cannot be changed later.
            </p>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <div class="flex">
              <ExclamationTriangleIcon class="h-5 w-5 text-red-400 shrink-0" />
              <div class="ml-3">
                <p class="text-sm text-red-700">{{ error }}</p>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-end gap-3">
            <BaseButton
              type="button"
              variant="secondary"
              @click="router.back()"
            >
              Cancel
            </BaseButton>
            <BaseButton
              type="submit"
              variant="primary"
              :loading="loading"
              :disabled="!isValid"
            >
              Create Organisation
            </BaseButton>
          </div>
        </form>
      </BaseCard>
    </div>
  </AppLayout>
</template>

<script setup>
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'
import BaseCard from '../components/BaseCard.vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PageHeader from '../components/layout/PageHeader.vue'
import api from '../lib/api'
import { useOrgStore } from '../stores/org'

const router = useRouter()
const orgStore = useOrgStore()

const form = reactive({
  name: '',
  slug: '',
})

const loading = ref(false)
const error = ref('')
const slugManuallyEdited = ref(false)

const isValid = computed(() => {
  return (
    form.name.trim().length >= 2 &&
    form.slug.trim().length >= 2 &&
    /^[a-z0-9-]+$/.test(form.slug)
  )
})

function generateSlug(name) {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 63)
}

function updateSlug() {
  if (!slugManuallyEdited.value) {
    form.slug = generateSlug(form.name)
  }
}

// Mark slug as manually edited when user types in it
function onSlugInput() {
  slugManuallyEdited.value = true
}

async function handleSubmit() {
  if (!isValid.value) return

  loading.value = true
  error.value = ''

  try {
    const response = await api.post('/organisations', {
      name: form.name.trim(),
      slug: form.slug.trim(),
    })

    const newOrg = response.data

    // Add to organisations list with owner role
    orgStore.organisations.push({
      ...newOrg,
      role: 'owner',
    })

    // Switch to the new organisation
    await orgStore.switchOrg(newOrg.id)

    // Navigate to the organisation settings page
    router.push({
      name: 'OrganisationSettings',
      params: { id: newOrg.id },
    })
  } catch (err) {
    console.error('Failed to create organisation:', err)
    if (err.response?.status === 409) {
      error.value =
        'An organisation with this slug already exists. Please choose a different slug.'
    } else if (err.response?.data?.detail) {
      error.value = err.response.data.detail
    } else {
      error.value = 'Failed to create organisation. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
