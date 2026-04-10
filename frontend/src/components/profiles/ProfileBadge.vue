<template>
  <span
    class="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium"
    :class="badgeClasses"
  >
    <span>{{ profileData?.name || 'Unknown Profile' }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useProfilesStore } from '../../stores/profiles'

const props = defineProps({
  profileId: {
    type: String,
    required: true,
  },
})

const profilesStore = useProfilesStore()

const profileData = computed(() => {
  return profilesStore.profiles.find((p) => p.id === props.profileId)
})

const badgeClasses = computed(() => {
  return profilesStore.getProfileBadgeClass(props.profileId)
})
</script>
