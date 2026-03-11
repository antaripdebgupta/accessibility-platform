<template>
  <div class="min-h-screen overflow-x-hidden bg-gray-50">
    <!-- Navigation bar -->
    <Navbar />

    <!-- Main content with top padding for fixed navbar -->
    <main class="mx-auto max-w-6xl px-4 py-8 pt-24 sm:px-6 lg:px-8">
      <slot></slot>
    </main>
  </div>
</template>

<script setup>
import Navbar from '../Navbar.vue'
</script>
