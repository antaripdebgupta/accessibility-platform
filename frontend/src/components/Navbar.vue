<template>
  <Disclosure
    as="nav"
    class="fixed left-0 right-0 top-0 z-50 bg-white border-b border-gray-200"
    v-slot="{ open }"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between">
        <!-- Logo -->
        <div class="flex items-center">
          <router-link to="/" class="flex items-center space-x-2">
            <div
              class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600"
            >
              <svg
                class="h-5 w-5 text-white"
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
            <span class="text-lg font-semibold text-gray-900">AccessHub</span>
          </router-link>
        </div>

        <!-- Desktop Auth Buttons -->
        <div class="hidden md:flex md:items-center md:space-x-3">
          <template v-if="!authStore.user">
            <BaseButton to="/signin" variant="ghost" size="sm"
              >Sign In</BaseButton
            >
            <BaseButton to="/signup" variant="primary" size="sm"
              >Get Started</BaseButton
            >
          </template>
          <template v-else>
            <Menu as="div" class="relative">
              <MenuButton
                class="flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
              >
                <div
                  class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-700 font-medium"
                >
                  {{ userInitials }}
                </div>
                <ChevronDownIcon class="h-4 w-4 text-gray-500" />
              </MenuButton>
              <transition
                enter-active-class="transition duration-100 ease-out"
                enter-from-class="transform scale-95 opacity-0"
                enter-to-class="transform scale-100 opacity-100"
                leave-active-class="transition duration-75 ease-in"
                leave-from-class="transform scale-100 opacity-100"
                leave-to-class="transform scale-95 opacity-0"
              >
                <MenuItems
                  class="absolute right-0 mt-2 w-56 origin-top-right rounded-xl bg-white border border-gray-200 shadow-medium focus:outline-none p-1"
                >
                  <div class="px-3 py-2 border-b border-gray-100">
                    <p class="text-sm font-medium text-gray-900">
                      {{ authStore.user?.email }}
                    </p>
                    <p class="text-xs text-gray-500">Signed in</p>
                  </div>
                  <div class="py-1">
                    <MenuItem v-slot="{ active }">
                      <router-link
                        to="/dashboard"
                        :class="[
                          active ? 'bg-gray-100' : '',
                          'flex items-center px-3 py-2 text-sm text-gray-700 rounded-lg',
                        ]"
                      >
                        <HomeIcon class="mr-2 h-4 w-4 text-gray-500" />
                        Dashboard
                      </router-link>
                    </MenuItem>
                    <MenuItem v-slot="{ active }">
                      <button
                        @click="handleLogout"
                        :class="[
                          active ? 'bg-gray-100' : '',
                          'flex w-full items-center px-3 py-2 text-sm text-gray-700 rounded-lg',
                        ]"
                      >
                        <ArrowRightOnRectangleIcon
                          class="mr-2 h-4 w-4 text-gray-500"
                        />
                        Sign Out
                      </button>
                    </MenuItem>
                  </div>
                </MenuItems>
              </transition>
            </Menu>
          </template>
        </div>

        <!-- Mobile menu button -->
        <div class="flex md:hidden">
          <DisclosureButton
            class="inline-flex items-center justify-center rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <span class="sr-only">Open main menu</span>
            <Bars3Icon v-if="!open" class="h-6 w-6" />
            <XMarkIcon v-else class="h-6 w-6" />
          </DisclosureButton>
        </div>
      </div>
    </div>

    <!-- Mobile menu panel -->
    <DisclosurePanel class="md:hidden border-t border-gray-200">
      <div class="space-y-1 px-4 py-3">
        <DisclosureButton
          v-for="item in navigation"
          :key="item.name"
          as="template"
        >
          <router-link
            :to="item.href"
            class="block rounded-lg px-3 py-2 text-base font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            active-class="bg-primary-50 text-primary-700"
          >
            {{ item.name }}
          </router-link>
        </DisclosureButton>
      </div>
      <div class="border-t border-gray-200 px-4 py-4">
        <template v-if="!authStore.user">
          <div class="flex flex-col space-y-2">
            <BaseButton to="/signin" variant="secondary" full-width
              >Sign In</BaseButton
            >
            <BaseButton to="/signup" variant="primary" full-width
              >Get Started</BaseButton
            >
          </div>
        </template>
        <template v-else>
          <div class="flex items-center mb-4">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-primary-700 font-medium"
            >
              {{ userInitials }}
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-gray-900">
                {{ authStore.user?.email }}
              </p>
              <p class="text-xs text-gray-500">Signed in</p>
            </div>
          </div>
          <BaseButton variant="secondary" full-width @click="handleLogout">
            Sign Out
          </BaseButton>
        </template>
      </div>
    </DisclosurePanel>
  </Disclosure>
</template>

<script setup>
import {
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
} from '@headlessui/vue'
import {
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  ChevronDownIcon,
  HomeIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import BaseButton from './BaseButton.vue'

const authStore = useAuthStore()
const router = useRouter()

const navigation = [{ name: 'Home', href: '/' }]

const userInitials = computed(() => {
  if (!authStore.user?.email) return '?'
  return authStore.user.email.charAt(0).toUpperCase()
})

async function handleLogout() {
  try {
    await authStore.logout()
    router.push({ name: 'Home' })
  } catch (err) {
    console.error('Logout failed:', err)
  }
}
</script>
