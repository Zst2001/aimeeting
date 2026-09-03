import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { createAppRouter, getSafeRedirectPath } from '@/router'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types/auth'

const authenticatedUser: User = {
  id: 12,
  username: 'zhangsan',
  employee_no: null,
  display_name: '张三',
  email: null,
  role: 'USER',
  status: 'ACTIVE',
}

describe('router authentication guard', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('redirects unauthenticated users from home to login', async () => {
    const authStore = useAuthStore()
    authStore.initialized = true
    const appRouter = createAppRouter()

    await appRouter.push('/')

    expect(appRouter.currentRoute.value.name).toBe('login')
    expect(appRouter.currentRoute.value.query.redirect).toBe('/')
  })

  it('redirects an authenticated user away from login', async () => {
    const authStore = useAuthStore()
    authStore.initialized = true
    authStore.user = authenticatedUser
    const appRouter = createAppRouter()

    await appRouter.push('/login')

    expect(appRouter.currentRoute.value.name).toBe('home')
  })

  it('only accepts same-origin redirect paths', () => {
    expect(getSafeRedirectPath('/')).toBe('/')
    expect(getSafeRedirectPath('/meetings')).toBe('/meetings')
    expect(getSafeRedirectPath('//external.example')).toBeUndefined()
    expect(getSafeRedirectPath('https://external.example')).toBeUndefined()
  })
})
