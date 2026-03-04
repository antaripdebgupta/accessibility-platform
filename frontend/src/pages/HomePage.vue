<template>
  <div class="min-h-[calc(100vh-4rem)] bg-linear-to-b from-gray-50 to-white">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
      <div class="text-center">
        <div class="inline-flex items-center rounded-full bg-primary-50 px-4 py-1.5 mb-6">
          <span class="text-sm font-medium text-primary-700">Making the web accessible for everyone</span>
        </div>

        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-gray-900">
          Accessibility
          <span class="text-primary-600">Platform</span>
        </h1>

        <p class="mt-6 text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
          Empowering developers and organizations to build inclusive digital experiences. 
          Test, monitor, and improve your web accessibility compliance.
        </p>

        <div class="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <BaseButton to="/signup" variant="primary" size="lg">
            Get Started Free
            <svg class="ml-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </BaseButton>

          <BaseButton to="/signin" variant="secondary" size="lg">
            Sign In
          </BaseButton>
        </div>
      </div>

      <div class="mt-24 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
        <div 
          v-for="feature in features" 
          :key="feature.title"
          class="relative group"
        >
          <BaseCard padding="lg" class="h-full transition-shadow hover:shadow-medium">
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 text-primary-600 mb-4">
              <component :is="feature.icon" class="h-6 w-6" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ feature.title }}</h3>
            <p class="text-gray-600 text-sm leading-relaxed">{{ feature.description }}</p>
          </BaseCard>
        </div>
      </div>
    </div>

    <footer class="border-t border-gray-200 bg-white">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <p class="text-center text-sm text-gray-500">
          &copy; 2026 AccessHub. Built with accessibility in mind.
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { h } from 'vue';
import BaseButton from '@/components/BaseButton.vue';
import BaseCard from '@/components/BaseCard.vue';

const CheckCircleIcon = () => h('svg', { class: 'h-6 w-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' })
]);

const ChartIcon = () => h('svg', { class: 'h-6 w-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' })
]);

const ShieldIcon = () => h('svg', { class: 'h-6 w-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' })
]);

const features = [
  {
    title: 'Automated Testing',
    description: 'Run comprehensive accessibility audits on your websites with industry-standard WCAG guidelines.',
    icon: CheckCircleIcon
  },
  {
    title: 'Detailed Reports',
    description: 'Get actionable insights with clear explanations and remediation steps for every issue found.',
    icon: ChartIcon
  },
  {
    title: 'Compliance Ready',
    description: 'Ensure your applications meet WCAG 2.1, ADA, and Section 508 compliance requirements.',
    icon: ShieldIcon
  }
];

</script>
