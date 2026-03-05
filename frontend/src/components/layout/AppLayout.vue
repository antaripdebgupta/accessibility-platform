<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation bar -->
    <AppNavbar />

    <!-- Main content with top padding for fixed navbar -->
    <main class="mx-auto max-w-5xl px-6 py-8 pt-24">
      <slot></slot>
    </main>
  </div>
</template>

<script setup>
import AppNavbar from './AppNavbar.vue'
</script>
