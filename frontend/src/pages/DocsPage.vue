<template>
  <div class="min-h-screen bg-white dark:bg-gray-950">
    <!-- Top Header -->
    <header
      class="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm dark:border-gray-800 dark:bg-gray-950/80"
    >
      <div
        class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8"
      >
        <div class="flex items-center gap-4">
          <router-link
            to="/"
            class="flex items-center gap-2 text-gray-900 dark:text-white"
          >
            <span class="font-semibold text-gray-900 dark:text-white"
              >AccessHub</span
            >
          </router-link>
          <span class="text-gray-300 dark:text-gray-700">/</span>
          <span class="text-sm text-gray-600 dark:text-gray-400">Docs</span>
        </div>

        <div class="flex items-center gap-4">
          <a
            href="https://github.com/antaripdebgupta/accessibility-platform"
            target="_blank"
            class="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path
                fill-rule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                clip-rule="evenodd"
              />
            </svg>
          </a>
          <router-link
            to="/signin"
            class="rounded-lg px-4 py-2 text-sm font-medium text-blue-600 outline-blue-600"
          >
            Get Started
          </router-link>
        </div>
      </div>
    </header>

    <div class="mx-auto max-w-[90rem]">
      <div class="flex">
        <!-- Left Sidebar -->
        <aside
          class="fixed top-14 hidden h-[calc(100vh-3.5rem)] w-64 shrink-0 overflow-y-auto border-r border-gray-200 bg-white px-4 py-8 dark:border-gray-800 dark:bg-gray-950 lg:block"
        >
          <nav class="space-y-8">
            <div>
              <h3
                class="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                Getting Started
              </h3>
              <ul class="space-y-1">
                <li>
                  <button
                    @click="navigateTo('introduction')"
                    :class="getLinkClass('introduction')"
                  >
                    Introduction
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('quick-start')"
                    :class="getLinkClass('quick-start')"
                  >
                    Quick Start
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('wcag-em')"
                    :class="getLinkClass('wcag-em')"
                  >
                    WCAG-EM Methodology
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('sampling')"
                    :class="getLinkClass('sampling')"
                  >
                    Sampling Algorithm
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h3
                class="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                For Auditors
              </h3>
              <ul class="space-y-1">
                <li>
                  <button
                    @click="navigateTo('running-evaluation')"
                    :class="getLinkClass('running-evaluation')"
                  >
                    Running Evaluations
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('disability-profiles')"
                    :class="getLinkClass('disability-profiles')"
                  >
                    Disability Profiles
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('verdicts')"
                    :class="getLinkClass('verdicts')"
                  >
                    Understanding Verdicts
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('reports')"
                    :class="getLinkClass('reports')"
                  >
                    Generating Reports
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h3
                class="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                For Developers
              </h3>
              <ul class="space-y-1">
                <li>
                  <button
                    @click="navigateTo('architecture')"
                    :class="getLinkClass('architecture')"
                  >
                    Architecture
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('tech-stack')"
                    :class="getLinkClass('tech-stack')"
                  >
                    Tech Stack
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('sse-events')"
                    :class="getLinkClass('sse-events')"
                  >
                    Real-Time SSE Events
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('api-docs')"
                    :class="getLinkClass('api-docs')"
                  >
                    API Documentation
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h3
                class="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                WCAG Reference
              </h3>
              <ul class="space-y-1">
                <li>
                  <button
                    @click="navigateTo('wcag-level-a')"
                    :class="getLinkClass('wcag-level-a')"
                  >
                    Level A Criteria
                  </button>
                </li>
                <li>
                  <button
                    @click="navigateTo('wcag-level-aa')"
                    :class="getLinkClass('wcag-level-aa')"
                  >
                    Level AA Criteria
                  </button>
                </li>
              </ul>
            </div>
          </nav>
        </aside>

        <!-- Main Content -->
        <main class="min-h-[calc(100vh-3.5rem)] flex-1 lg:pl-64">
          <div class="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
            <!-- Introduction -->
            <section id="introduction" class="scroll-mt-20">
              <h1
                class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Introduction
              </h1>
              <p class="mt-4 text-lg text-gray-600 dark:text-gray-400">
                Welcome to the WCAG Accessibility Evaluation Platform
                documentation. This platform helps you evaluate websites for
                WCAG 2.1 compliance using the official W3C evaluation
                methodology.
              </p>
              <div
                class="mt-8 rounded-xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-800/50 dark:bg-blue-900/20"
              >
                <h3
                  class="flex items-center gap-2 text-base font-semibold text-blue-900 dark:text-blue-100"
                >
                  What is WCAG?
                </h3>
                <p class="mt-2 text-sm text-blue-800 dark:text-blue-200">
                  The Web Content Accessibility Guidelines (WCAG) are
                  international standards for making web content accessible to
                  people with disabilities. WCAG 2.1 includes guidelines
                  organized under four principles: Perceivable, Operable,
                  Understandable, and Robust.
                </p>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Quick Start -->
            <section id="quick-start" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Quick Start
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Get started with your first accessibility evaluation in three
                simple steps.
              </p>
              <div class="mt-8 space-y-6">
                <div class="flex gap-4">
                  <div
                    class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white"
                  >
                    1
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900 dark:text-white">
                      Create an Account
                    </h3>
                    <p class="mt-1 text-gray-600 dark:text-gray-400">
                      Sign up for free to access the full evaluation workflow
                      and team collaboration features.
                    </p>
                  </div>
                </div>
                <div class="flex gap-4">
                  <div
                    class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white"
                  >
                    2
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900 dark:text-white">
                      Create an Evaluation
                    </h3>
                    <p class="mt-1 text-gray-600 dark:text-gray-400">
                      Enter your target URL and let our automated crawler
                      discover all pages on your website.
                    </p>
                  </div>
                </div>
                <div class="flex gap-4">
                  <div
                    class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white"
                  >
                    3
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900 dark:text-white">
                      Review and Report
                    </h3>
                    <p class="mt-1 text-gray-600 dark:text-gray-400">
                      Review findings, assign verdicts, and generate
                      comprehensive WCAG-EM conformance reports.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- WCAG-EM -->
            <section id="wcag-em" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                WCAG-EM Methodology
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                This platform implements the
                <a
                  href="https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/"
                  target="_blank"
                  class="text-blue-600 underline hover:text-blue-700 dark:text-blue-400"
                  >W3C Website Accessibility Conformance Evaluation
                  Methodology</a
                >
                — the international standard for evaluating website
                accessibility.
              </p>
              <div class="mt-8 space-y-4">
                <div
                  v-for="(step, index) in wcagEmSteps"
                  :key="index"
                  class="rounded-lg border border-gray-200 p-4 dark:border-gray-800"
                >
                  <div class="flex items-start gap-4">
                    <div
                      class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white dark:bg-white dark:text-gray-900"
                    >
                      {{ index + 1 }}
                    </div>
                    <div>
                      <h4 class="font-semibold text-gray-900 dark:text-white">
                        {{ step.title }}
                      </h4>
                      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        {{ step.description }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Sampling Algorithm -->
            <section id="sampling" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Sampling Algorithm
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Our platform uses an intelligent sampling algorithm based on
                WCAG-EM guidelines to select a representative sample of pages
                for evaluation.
              </p>
              <div
                class="mt-8 rounded-xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-900/50"
              >
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  How Sampling Works
                </h3>
                <ol class="mt-4 space-y-3 text-gray-600 dark:text-gray-400">
                  <li class="flex gap-3">
                    <span class="font-mono text-blue-600 dark:text-blue-400"
                      >1.</span
                    >
                    <span
                      ><strong class="text-gray-900 dark:text-white"
                        >Page Classification</strong
                      >
                      — Pages are categorized by template type (homepage,
                      listing, detail, form, etc.) based on URL patterns and DOM
                      structure.</span
                    >
                  </li>
                  <li class="flex gap-3">
                    <span class="font-mono text-blue-600 dark:text-blue-400"
                      >2.</span
                    >
                    <span
                      ><strong class="text-gray-900 dark:text-white"
                        >Stratified Selection</strong
                      >
                      — At least one page from each template category is
                      included to ensure coverage across different page
                      types.</span
                    >
                  </li>
                  <li class="flex gap-3">
                    <span class="font-mono text-blue-600 dark:text-blue-400"
                      >3.</span
                    >
                    <span
                      ><strong class="text-gray-900 dark:text-white"
                        >Essential Pages</strong
                      >
                      — Critical pages (homepage, contact, login, search
                      results) are always included in the sample.</span
                    >
                  </li>
                  <li class="flex gap-3">
                    <span class="font-mono text-blue-600 dark:text-blue-400"
                      >4.</span
                    >
                    <span
                      ><strong class="text-gray-900 dark:text-white"
                        >Random Selection</strong
                      >
                      — Additional pages are randomly selected to meet the
                      minimum sample size (typically 10-20% of total pages,
                      minimum 5).</span
                    >
                  </li>
                </ol>
              </div>
              <div
                class="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-800/50 dark:bg-amber-900/20"
              >
                <h4
                  class="flex items-center gap-2 text-sm font-semibold text-amber-900 dark:text-amber-100"
                >
                  Manual Override
                </h4>
                <p class="mt-1 text-sm text-amber-800 dark:text-amber-200">
                  You can always manually add or remove pages from the sample
                  before running the accessibility scan.
                </p>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Running Evaluations -->
            <section id="running-evaluation" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Running Evaluations
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                As an auditor, follow this workflow to complete a comprehensive
                accessibility evaluation.
              </p>
              <ol class="mt-6 space-y-4 text-gray-600 dark:text-gray-400">
                <li class="flex gap-3">
                  <span class="font-mono text-blue-600 dark:text-blue-400"
                    >1.</span
                  ><span
                    ><strong class="text-gray-900 dark:text-white"
                      >Create evaluation</strong
                    >
                    — Enter the target website URL and a descriptive
                    title.</span
                  >
                </li>
                <li class="flex gap-3">
                  <span class="font-mono text-blue-600 dark:text-blue-400"
                    >2.</span
                  ><span
                    ><strong class="text-gray-900 dark:text-white"
                      >Start exploration</strong
                    >
                    — Our crawler discovers all accessible pages with real-time
                    progress.</span
                  >
                </li>
                <li class="flex gap-3">
                  <span class="font-mono text-blue-600 dark:text-blue-400"
                    >3.</span
                  ><span
                    ><strong class="text-gray-900 dark:text-white"
                      >Review sample</strong
                    >
                    — Use WCAG-EM sampling or manually select representative
                    pages.</span
                  >
                </li>
                <li class="flex gap-3">
                  <span class="font-mono text-blue-600 dark:text-blue-400"
                    >4.</span
                  ><span
                    ><strong class="text-gray-900 dark:text-white"
                      >Run scan</strong
                    >
                    — axe-core tests all WCAG 2.1 Level A and AA criteria.</span
                  >
                </li>
                <li class="flex gap-3">
                  <span class="font-mono text-blue-600 dark:text-blue-400"
                    >5.</span
                  ><span
                    ><strong class="text-gray-900 dark:text-white"
                      >Review findings</strong
                    >
                    — Confirm, dismiss, or mark findings for manual
                    review.</span
                  >
                </li>
                <li class="flex gap-3">
                  <span class="font-mono text-blue-600 dark:text-blue-400"
                    >6.</span
                  ><span
                    ><strong class="text-gray-900 dark:text-white"
                      >Generate report</strong
                    >
                    — Export PDF, CSV, or EARL format reports.</span
                  >
                </li>
              </ol>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Disability Profiles -->
            <section id="disability-profiles" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Disability Profiles
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Use disability profiles to prioritize findings based on user
                impact.
              </p>
              <div class="mt-8 grid gap-4 sm:grid-cols-2">
                <div
                  v-for="profile in disabilityProfiles"
                  :key="profile.name"
                  class="rounded-lg border border-gray-200 p-4 dark:border-gray-800"
                >
                  <h4 class="font-semibold text-gray-900 dark:text-white">
                    {{ profile.name }}
                  </h4>
                  <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    {{ profile.description }}
                  </p>
                </div>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Verdicts -->
            <section id="verdicts" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Understanding Verdicts
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Each WCAG criterion receives a verdict indicating its
                conformance status.
              </p>
              <div
                class="mt-8 overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800"
              >
                <table class="w-full text-left text-sm">
                  <thead class="bg-gray-50 dark:bg-gray-800/50">
                    <tr>
                      <th
                        class="px-4 py-3 font-semibold text-gray-900 dark:text-white"
                      >
                        Verdict
                      </th>
                      <th
                        class="px-4 py-3 font-semibold text-gray-900 dark:text-white"
                      >
                        Meaning
                      </th>
                      <th
                        class="hidden px-4 py-3 font-semibold text-gray-900 dark:text-white sm:table-cell"
                      >
                        When to Use
                      </th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
                    <tr v-for="verdict in verdicts" :key="verdict.name">
                      <td class="px-4 py-3">
                        <span :class="verdict.class">{{ verdict.name }}</span>
                      </td>
                      <td class="px-4 py-3 text-gray-600 dark:text-gray-400">
                        {{ verdict.meaning }}
                      </td>
                      <td
                        class="hidden px-4 py-3 text-gray-600 dark:text-gray-400 sm:table-cell"
                      >
                        {{ verdict.usage }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Reports -->
            <section id="reports" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Generating Reports
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Export your evaluation results in multiple formats.
              </p>
              <div class="mt-8 grid gap-4 sm:grid-cols-3">
                <div
                  class="rounded-lg border border-gray-200 p-4 dark:border-gray-800"
                >
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"
                  >
                    <svg
                      class="h-5 w-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  </div>
                  <h4 class="mt-3 font-semibold text-gray-900 dark:text-white">
                    PDF Report
                  </h4>
                  <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    Professional conformance report with executive summary.
                  </p>
                </div>
                <div
                  class="rounded-lg border border-gray-200 p-4 dark:border-gray-800"
                >
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400"
                  >
                    <svg
                      class="h-5 w-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  </div>
                  <h4 class="mt-3 font-semibold text-gray-900 dark:text-white">
                    CSV Export
                  </h4>
                  <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    Raw data export for spreadsheet analysis.
                  </p>
                </div>
                <div
                  class="rounded-lg border border-gray-200 p-4 dark:border-gray-800"
                >
                  <div
                    class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400"
                  >
                    <svg
                      class="h-5 w-5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  </div>
                  <h4 class="mt-3 font-semibold text-gray-900 dark:text-white">
                    EARL (JSON-LD)
                  </h4>
                  <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    W3C standard machine-readable format.
                  </p>
                </div>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Architecture -->
            <section id="architecture" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Architecture
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                High-level overview of the platform architecture.
              </p>
              <div class="mt-8 overflow-x-auto rounded-lg bg-gray-900 p-4">
                <pre
                  class="text-xs text-gray-100 sm:text-sm"
                ><code>┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Browser   │────▶│    Nginx    │────▶│   Vue SPA    │
└─────────────┘     │   Proxy     │     └──────────────┘
                    │             │     ┌──────────────┐
                    │             │────▶│   FastAPI    │
                    └─────────────┘     └──────┬───────┘
                                               │
         ┌─────────────────────────────────────┼─────────────────────────────────────┐
         │                                     │                                     │
         ▼                                     ▼                                     ▼
 ┌──────────────┐                     ┌──────────────┐                     ┌──────────────┐
 │  PostgreSQL  │                     │    Redis     │                     │    MinIO     │
 └──────────────┘                     └──────┬───────┘                     └──────────────┘
                                             │
                                             ▼
                                     ┌──────────────┐
                                     │   Celery     │
                                     └──────────────┘</code></pre>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- Tech Stack -->
            <section id="tech-stack" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Tech Stack
              </h2>
              <div class="mt-8 grid gap-6 sm:grid-cols-2">
                <div>
                  <h3
                    class="text-lg font-semibold text-gray-900 dark:text-white"
                  >
                    Backend
                  </h3>
                  <ul class="mt-4 space-y-2 text-gray-600 dark:text-gray-400">
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-blue-600"></span
                      >FastAPI (async Python 3.12)
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-blue-600"></span
                      >PostgreSQL with Row-Level Security
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-blue-600"></span
                      >Redis for task queue and SSE
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-blue-600"></span
                      >Celery for async processing
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-blue-600"></span
                      >Playwright for browser automation
                    </li>
                  </ul>
                </div>
                <div>
                  <h3
                    class="text-lg font-semibold text-gray-900 dark:text-white"
                  >
                    Frontend
                  </h3>
                  <ul class="mt-4 space-y-2 text-gray-600 dark:text-gray-400">
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-green-600"></span
                      >Vue 3 (Composition API)
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-green-600"></span
                      >Pinia state management
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-green-600"></span
                      >Tailwind CSS
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-green-600"></span
                      >Firebase Auth SDK
                    </li>
                    <li class="flex items-center gap-2">
                      <span class="h-1.5 w-1.5 rounded-full bg-green-600"></span
                      >EventSource API for SSE
                    </li>
                  </ul>
                </div>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- SSE Events -->
            <section id="sse-events" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                Real-Time SSE Events
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Server-Sent Events provide real-time updates for long-running
                tasks.
              </p>
              <div class="mt-6 rounded-lg bg-gray-900 p-4">
                <span class="text-xs text-gray-400">JavaScript</span>
                <pre
                  class="mt-2 overflow-x-auto text-sm text-gray-100"
                ><code>const evtSource = new EventSource(
  '/api/v1/tasks/' + taskId + '/stream'
);
evtSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.percent, '%');
};</code></pre>
              </div>
              <h3
                class="mt-8 text-lg font-semibold text-gray-900 dark:text-white"
              >
                Event Types
              </h3>
              <div class="mt-4 space-y-3">
                <div class="flex items-center gap-3">
                  <code
                    class="rounded bg-gray-100 px-2 py-1 text-sm dark:bg-gray-800"
                    >progress</code
                  ><span class="text-gray-600 dark:text-gray-400"
                    >Task progress updates (0-100%)</span
                  >
                </div>
                <div class="flex items-center gap-3">
                  <code
                    class="rounded bg-gray-100 px-2 py-1 text-sm dark:bg-gray-800"
                    >complete</code
                  ><span class="text-gray-600 dark:text-gray-400"
                    >Task completed successfully</span
                  >
                </div>
                <div class="flex items-center gap-3">
                  <code
                    class="rounded bg-gray-100 px-2 py-1 text-sm dark:bg-gray-800"
                    >error</code
                  ><span class="text-gray-600 dark:text-gray-400"
                    >Task failed with error</span
                  >
                </div>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- API Documentation -->
            <section id="api-docs" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                API Documentation
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Our REST API is fully documented with interactive documentation.
                Explore all available endpoints, request/response schemas, and
                try out API calls directly in your browser.
              </p>
              <div class="mt-8 grid gap-4 sm:grid-cols-2">
                <a
                  href="/api/v1/docs"
                  target="_blank"
                  class="group rounded-lg border border-gray-200 p-6 transition-colors hover:border-blue-300 hover:bg-blue-50 dark:border-gray-800 dark:hover:border-blue-700 dark:hover:bg-blue-900/20"
                >
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400"
                    >
                      <svg
                        class="h-5 w-5"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z"
                          clip-rule="evenodd"
                        />
                      </svg>
                    </div>
                    <div>
                      <h4
                        class="font-semibold text-gray-900 group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400"
                      >
                        Swagger UI
                      </h4>
                      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        Interactive API explorer with try-it-out functionality
                      </p>
                    </div>
                  </div>
                </a>
                <a
                  href="/api/v1/redoc"
                  target="_blank"
                  class="group rounded-lg border border-gray-200 p-6 transition-colors hover:border-blue-300 hover:bg-blue-50 dark:border-gray-800 dark:hover:border-blue-700 dark:hover:bg-blue-900/20"
                >
                  <div class="flex items-center gap-3">
                    <div
                      class="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400"
                    >
                      <svg
                        class="h-5 w-5"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                          clip-rule="evenodd"
                        />
                      </svg>
                    </div>
                    <div>
                      <h4
                        class="font-semibold text-gray-900 group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400"
                      >
                        ReDoc
                      </h4>
                      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        Clean, readable API reference documentation
                      </p>
                    </div>
                  </div>
                </a>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- WCAG Level A -->
            <section id="wcag-level-a" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                WCAG Level A Criteria
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Level A is the minimum conformance level. These are essential
                requirements.
              </p>
              <div class="mt-6 space-y-3">
                <div
                  v-for="criterion in wcagLevelA"
                  :key="criterion.id"
                  class="rounded-lg border border-gray-200 p-4 dark:border-gray-800"
                >
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <h4 class="font-semibold text-gray-900 dark:text-white">
                        <span class="mr-2 text-blue-600 dark:text-blue-400">{{
                          criterion.id
                        }}</span
                        >{{ criterion.name }}
                      </h4>
                      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        {{ criterion.description }}
                      </p>
                    </div>
                    <span
                      class="shrink-0 rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900/50 dark:text-blue-300"
                      >A</span
                    >
                  </div>
                </div>
              </div>
            </section>

            <hr class="my-12 border-gray-200 dark:border-gray-800" />

            <!-- WCAG Level AA -->
            <section id="wcag-level-aa" class="scroll-mt-20">
              <h2
                class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white"
              >
                WCAG Level AA Criteria
              </h2>
              <p class="mt-4 text-gray-600 dark:text-gray-400">
                Level AA is the recommended conformance level for most websites.
              </p>
              <div class="mt-6 space-y-3">
                <div
                  v-for="criterion in wcagLevelAA"
                  :key="criterion.id"
                  class="rounded-lg border border-gray-200 p-4 dark:border-gray-800"
                >
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <h4 class="font-semibold text-gray-900 dark:text-white">
                        <span class="mr-2 text-amber-600 dark:text-amber-400">{{
                          criterion.id
                        }}</span
                        >{{ criterion.name }}
                      </h4>
                      <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        {{ criterion.description }}
                      </p>
                    </div>
                    <span
                      class="shrink-0 rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/50 dark:text-amber-300"
                      >AA</span
                    >
                  </div>
                </div>
              </div>
            </section>

            <!-- Footer -->
            <footer
              class="mt-16 border-t border-gray-200 pt-8 dark:border-gray-800"
            >
              <div
                class="flex flex-col items-center justify-between gap-4 sm:flex-row"
              >
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  © {{ new Date().getFullYear() }} WCAG Accessibility Evaluation
                  Platform
                </p>
                <div class="flex gap-4">
                  <a
                    href="https://www.w3.org/WAI/standards-guidelines/wcag/"
                    target="_blank"
                    class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                    >WCAG Guidelines</a
                  >
                  <a
                    href="https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/"
                    target="_blank"
                    class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                    >WCAG-EM</a
                  >
                </div>
              </div>
            </footer>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const activeSection = ref('introduction')

const allSections = [
  'introduction',
  'quick-start',
  'wcag-em',
  'sampling',
  'running-evaluation',
  'disability-profiles',
  'verdicts',
  'reports',
  'architecture',
  'tech-stack',
  'sse-events',
  'api-docs',
  'wcag-level-a',
  'wcag-level-aa',
]

const navigateTo = (id) => {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeSection.value = id
  }
}

const getLinkClass = (id) => {
  const base =
    'block w-full text-left px-3 py-1.5 text-sm rounded-md transition-colors'
  return activeSection.value === id
    ? `${base} bg-blue-50 text-blue-700 font-medium dark:bg-blue-900/30 dark:text-blue-400`
    : `${base} text-gray-600 hover:text-gray-900 hover:bg-gray-50 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800`
}

let observer = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          activeSection.value = entry.target.id
        }
      })
    },
    { rootMargin: '-20% 0px -70% 0px', threshold: 0 },
  )
  allSections.forEach((id) => {
    const el = document.getElementById(id)
    if (el) observer.observe(el)
  })
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})

const wcagEmSteps = [
  {
    title: 'Define Evaluation Scope',
    description:
      'Set the target URL, conformance level, and evaluation parameters.',
  },
  {
    title: 'Explore the Website',
    description:
      'Automatically crawl and discover pages using our Playwright spider.',
  },
  {
    title: 'Select Representative Sample',
    description: 'Choose pages using our WCAG-EM sampling algorithm.',
  },
  {
    title: 'Audit the Sample',
    description: 'Run automated axe-core scans and perform manual review.',
  },
  {
    title: 'Report Findings',
    description:
      'Generate PDF, CSV, and EARL reports with conformance verdicts.',
  },
]

const disabilityProfiles = [
  {
    name: 'Screen Reader',
    description:
      'Prioritizes text alternatives, semantic structure, and programmatic labels.',
  },
  {
    name: 'Low Vision',
    description:
      'Prioritizes contrast ratios, text resizing, and content reflow.',
  },
  {
    name: 'Motor Impairment',
    description: 'Prioritizes keyboard accessibility and focus management.',
  },
  {
    name: 'Cognitive',
    description: 'Prioritizes consistent navigation and clear labels.',
  },
]

const verdicts = [
  {
    name: 'Pass',
    meaning: 'Criterion is satisfied',
    usage: 'All instances pass checks',
    class:
      'rounded bg-green-100 px-2 py-1 text-xs font-medium text-green-700 dark:bg-green-900/50 dark:text-green-300',
  },
  {
    name: 'Fail',
    meaning: 'Accessibility barrier found',
    usage: 'Confirmed issues exist',
    class:
      'rounded bg-red-100 px-2 py-1 text-xs font-medium text-red-700 dark:bg-red-900/50 dark:text-red-300',
  },
  {
    name: 'Cannot Tell',
    meaning: 'Manual review needed',
    usage: 'Automation inconclusive',
    class:
      'rounded bg-amber-100 px-2 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/50 dark:text-amber-300',
  },
  {
    name: 'N/A',
    meaning: 'Not applicable',
    usage: 'Content type mismatch',
    class:
      'rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  },
]

const wcagLevelA = [
  {
    id: '1.1.1',
    name: 'Non-text Content',
    description: 'All non-text content has a text alternative.',
  },
  {
    id: '1.3.1',
    name: 'Info and Relationships',
    description:
      'Information and structure can be programmatically determined.',
  },
  {
    id: '2.1.1',
    name: 'Keyboard',
    description: 'All functionality is available from a keyboard.',
  },
  {
    id: '2.4.1',
    name: 'Bypass Blocks',
    description: 'A mechanism is available to bypass repeated content.',
  },
  {
    id: '4.1.2',
    name: 'Name, Role, Value',
    description: 'UI components have accessible names and roles.',
  },
]

const wcagLevelAA = [
  {
    id: '1.4.3',
    name: 'Contrast (Minimum)',
    description: 'Text has a contrast ratio of at least 4.5:1.',
  },
  {
    id: '1.4.4',
    name: 'Resize Text',
    description: 'Text can be resized up to 200% without loss.',
  },
  {
    id: '2.4.6',
    name: 'Headings and Labels',
    description: 'Headings and labels describe topic or purpose.',
  },
  {
    id: '2.4.7',
    name: 'Focus Visible',
    description: 'Keyboard focus indicator is visible.',
  },
  {
    id: '3.3.2',
    name: 'Labels or Instructions',
    description: 'Labels are provided when input is required.',
  },
]
</script>
