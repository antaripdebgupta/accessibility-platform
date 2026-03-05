import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../pages/HomePage.vue'),
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
