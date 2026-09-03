import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/api/auth', () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  refresh: vi.fn(),
}))

import * as authApi from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types/auth'
import { getAccessToken, getRefreshToken, setTokens } from '@/utils/tokenStorage'

const currentUser: User = {
  id: 12,
  username: 'zhangsan',
  employee_no: 'E0012',
  display_name: '张三',
  email: 'zhangsan@example.test',
  role: 'USER',
  status: 'ACTIVE',
}

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('logs in, stores a complete token pair, and loads /me as the user source of truth', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'access-a',
      refresh_token: 'refresh-a',
      token_type: 'bearer',
      expires_in: 1800,
      user: { id: 12, username: 'zhangsan', display_name: '张三', role: 'USER' },
    })
    vi.mocked(authApi.getMe).mockResolvedValue(currentUser)

    const store = useAuthStore()
    await store.login({ username: 'zhangsan', password: 'CorrectPassword123!' })

    expect(getAccessToken()).toBe('access-a')
    expect(getRefreshToken()).toBe('refresh-a')
    expect(store.user).toEqual(currentUser)
    expect(store.isAuthenticated).toBe(true)
  })

  it('does not preserve credentials when login fails', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('invalid credentials'))

    const store = useAuthStore()
    await expect(store.login({ username: 'zhangsan', password: 'WrongPassword123!' })).rejects.toThrow(
      'invalid credentials',
    )

    expect(store.user).toBeNull()
    expect(getAccessToken()).toBeNull()
  })

  it('bootstraps without a token without calling /me', async () => {
    const store = useAuthStore()
    await store.bootstrap()

    expect(authApi.getMe).not.toHaveBeenCalled()
    expect(store.initialized).toBe(true)
    expect(store.isAuthenticated).toBe(false)
  })

  it('restores a valid browser session by loading /me', async () => {
    setTokens('access-existing', 'refresh-existing')
    vi.mocked(authApi.getMe).mockResolvedValue(currentUser)

    const store = useAuthStore()
    await store.bootstrap()

    expect(authApi.getMe).toHaveBeenCalledOnce()
    expect(store.user).toEqual(currentUser)
    expect(store.initialized).toBe(true)
  })

  it('clears local state even when backend logout fails', async () => {
    setTokens('access-a', 'refresh-a')
    vi.mocked(authApi.getMe).mockResolvedValue(currentUser)
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network error'))
    const store = useAuthStore()
    await store.fetchMe()

    await expect(store.logout()).rejects.toThrow('network error')

    expect(store.user).toBeNull()
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
    expect(store.initialized).toBe(true)
  })
})
