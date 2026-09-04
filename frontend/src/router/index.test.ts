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

  it('redirects unauthenticated users from the meeting list to login', async () => {
    const authStore = useAuthStore()
    authStore.initialized = true
    const appRouter = createAppRouter()

    await appRouter.push('/meetings')

    expect(appRouter.currentRoute.value.name).toBe('login')
    expect(appRouter.currentRoute.value.query.redirect).toBe('/meetings')
  })

  it('redirects an authenticated user away from login', async () => {
    const authStore = useAuthStore()
    authStore.initialized = true
    authStore.user = authenticatedUser
    const appRouter = createAppRouter()

    await appRouter.push('/login')

    expect(appRouter.currentRoute.value.name).toBe('meetings')
  })

  it('marks the meeting detail route as protected', async () => {
    const authStore = useAuthStore()
    authStore.initialized = true
    const appRouter = createAppRouter()

    await appRouter.push('/meetings/99')

    expect(appRouter.currentRoute.value.name).toBe('login')
    expect(appRouter.currentRoute.value.query.redirect).toBe('/meetings/99')
  })

  it('redirects the normal root entry to the meeting list after authentication', async () => {
    const authStore = useAuthStore()
    authStore.initialized = true
    authStore.user = authenticatedUser
    const appRouter = createAppRouter()

    await appRouter.push('/')

    expect(appRouter.currentRoute.value.name).toBe('meetings')
  })

  it('only accepts same-origin redirect paths', () => {
    expect(getSafeRedirectPath('/')).toBe('/')
    expect(getSafeRedirectPath('/meetings')).toBe('/meetings')
    expect(getSafeRedirectPath('//external.example')).toBeUndefined()
    expect(getSafeRedirectPath('https://external.example')).toBeUndefined()
  })
})
