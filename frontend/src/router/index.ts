import { createRouter, createWebHistory, type Router } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
export { getSafeRedirectPath } from '@/utils/navigation'
import LoginView from '@/views/auth/LoginView.vue'
import HomeView from '@/views/HomeView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
  }
}

export function createAppRouter(): Router {
  const appRouter = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/',
        name: 'home',
        component: HomeView,
        meta: { requiresAuth: true },
      },
      {
        path: '/login',
        name: 'login',
        component: LoginView,
      },
    ],
  })

  appRouter.beforeEach(async (to) => {
    const authStore = useAuthStore()
    if (!authStore.initialized) {
      await authStore.bootstrap()
    }

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      return {
        name: 'login',
        query: { redirect: to.fullPath },
      }
    }
    if (to.name === 'login' && authStore.isAuthenticated) {
      return { name: 'home' }
    }
    return true
  })

  return appRouter
}

export const router = createAppRouter()
