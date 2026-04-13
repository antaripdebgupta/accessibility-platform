import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../pages/HomePage.vue'),
  },
  {
    path: '/docs',
    name: 'Docs',
    component: () => import('../pages/DocsPage.vue'),
  },
  {
    path: '/signin',
    name: 'SignIn',
    component: () => import('../pages/SignInPage.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/login',
    name: 'Login',
    redirect: '/signin',
  },
  {
    path: '/signup',
    name: 'SignUp',
    component: () => import('../pages/SignUpPage.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../pages/DashboardPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/evaluations/new',
    name: 'EvaluationCreate',
    component: () => import('../pages/EvaluationCreatePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/evaluations/:id',
    name: 'EvaluationDetail',
    component: () => import('../pages/EvaluationDetailPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/evaluations/:id/explore',
    name: 'Exploration',
    component: () => import('../pages/ExplorationPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/evaluations/:id/sample',
    name: 'Sampling',
    component: () => import('../pages/SamplingPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/evaluations/:id/findings',
    name: 'Findings',
    component: () => import('../pages/FindingsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/evaluations/:id/reports',
    name: 'Reports',
    component: () => import('../pages/ReportsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/organisations/new',
    name: 'OrganisationCreate',
    component: () => import('../pages/OrganisationCreatePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/organisations/:id',
    name: 'OrganisationSettings',
    component: () => import('../pages/OrganisationPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/longitudinal',
    name: 'Longitudinal',
    component: () => import('../pages/LongitudinalPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/invitations/:token',
    name: 'InvitationAccept',
    component: () => import('../pages/InvitationAcceptPage.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../pages/NotFoundPage.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (!authStore.initialized) {
    await authStore.initAuthListener()
  }

  const isAuthenticated = authStore.isAuthenticated

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({
      name: 'SignIn',
      query: { redirect: to.fullPath },
    })
    return
  }

  if (to.meta.requiresGuest && isAuthenticated) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router
