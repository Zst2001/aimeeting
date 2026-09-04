import { createRouter, createWebHistory, type Router } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
export { getSafeRedirectPath } from '@/utils/navigation'
import LoginView from '@/views/auth/LoginView.vue'
import MeetingDetailView from '@/views/meetings/MeetingDetailView.vue'
import MeetingListView from '@/views/meetings/MeetingListView.vue'

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
        redirect: { name: 'meetings' },
      },
      {
        path: '/meetings',
        name: 'meetings',
        component: MeetingListView,
        meta: { requiresAuth: true },
      },
      {
        path: '/meetings/:meetingId',
        name: 'meeting-detail',
        component: MeetingDetailView,
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
      return { name: 'meetings' }
    }
    return true
  })

  return appRouter
}

export const router = createAppRouter()
