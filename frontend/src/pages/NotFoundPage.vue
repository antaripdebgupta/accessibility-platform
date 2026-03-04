<template>
  <div
    class="min-h-screen flex flex-col items-center justify-center bg-gray-100"
  >
    <h1 class="text-3xl font-bold text-gray-800 mb-2">404 - Not Found</h1>
    <p class="text-gray-600 mb-6">
      The page you are looking for does not exist.
    </p>
    <router-link
      to="/"
      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
      >Go Home</router-link
    >
  </div>
</template>

<script setup>
// Minimal NotFound page
</script>
