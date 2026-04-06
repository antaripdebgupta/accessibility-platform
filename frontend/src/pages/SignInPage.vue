<template>
  <div
    class="min-h-[calc(100vh-4rem)] flex items-center justify-center bg-gray-50 px-4 py-12"
  >
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="flex justify-center mb-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-600"
          >
            <svg
              class="h-7 w-7 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
          </div>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Welcome back</h1>
        <p class="mt-2 text-sm text-gray-600">
          Sign in to your account to continue
        </p>
      </div>

      <BaseCard padding="lg">
        <form @submit.prevent="onSubmit" class="space-y-5">
          <BaseInput
            id="email"
            type="email"
            label="Email address"
            placeholder="you@example.com"
            v-model="email"
            :disabled="loading"
            :error="fieldErrors.email"
            required
          />

          <BaseInput
            id="password"
            type="password"
            label="Password"
            placeholder="Enter your password"
            v-model="password"
            :disabled="loading"
            :error="fieldErrors.password"
            required
          />

          <div
            v-if="error"
            class="rounded-lg bg-red-50 border border-red-200 p-4"
            role="alert"
          >
            <div class="flex">
              <svg
                class="h-5 w-5 text-red-500 mr-2 shrink-0"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
              <p class="text-sm text-red-700">{{ error }}</p>
            </div>
          </div>

          <BaseButton
            variant="primary"
            type="submit"
            :loading="loading"
            :disabled="loading"
            full-width
          >
            Sign In
          </BaseButton>
        </form>

        <div class="relative mt-6">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-200"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="bg-white px-4 text-gray-500">New to AccessHub?</span>
          </div>
        </div>

        <div class="mt-6">
          <BaseButton to="/signup" variant="secondary" full-width>
            Create an account
          </BaseButton>
        </div>
      </BaseCard>
    </div>
  </div>
</template>

<script setup>
import BaseButton from '@/components/BaseButton.vue'
import BaseCard from '@/components/BaseCard.vue'
import BaseInput from '@/components/BaseInput.vue'
import { signInWithEmailAndPassword } from 'firebase/auth'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth } from '../lib/firebase'
import { validateAuthInput } from '../lib/validators/auth'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const fieldErrors = reactive({ email: '', password: '' })
const route = useRoute()
const router = useRouter()

function clearFieldErrors() {
  fieldErrors.email = ''
  fieldErrors.password = ''
}

function friendlyFirebaseError(err) {
  const code = err?.code || ''
  switch (code) {
    case 'auth/user-not-found':
      return 'No account found for this email.'
    case 'auth/wrong-password':
      return 'Incorrect password.'
    case 'auth/invalid-credential':
      return 'Invalid email or password.'
    case 'auth/too-many-requests':
      return 'Too many attempts. Please try again later.'
    default:
      return (err && err.message) || 'An unexpected error occurred.'
  }
}

async function onSubmit() {
  error.value = ''
  clearFieldErrors()

  const validation = validateAuthInput({
    email: email.value,
    password: password.value,
  })

  if (!validation.success) {
    error.value = validation.errors.join(' ')
    return
  }

  loading.value = true
  try {
    await signInWithEmailAndPassword(auth, email.value, password.value)
    // Check for redirect query param (e.g., from invitation accept flow)
    const redirectPath = route.query.redirect
    if (
      redirectPath &&
      typeof redirectPath === 'string' &&
      redirectPath.startsWith('/')
    ) {
      router.push(redirectPath)
    } else {
      router.push({ name: 'Dashboard' })
    }
  } catch (err) {
    error.value = friendlyFirebaseError(err)
  } finally {
    loading.value = false
  }
}
</script>
