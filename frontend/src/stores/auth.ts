import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getMe, login as loginApi, logout as logoutApi } from '@/api/auth'
import type { LoginRequest, User } from '@/types/auth'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/tokenStorage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const initialized = ref(false)
  let bootstrapPromise: Promise<void> | null = null

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  function clearAuth(): void {
    clearTokens()
    user.value = null
  }

  async function fetchMe(): Promise<User> {
    const currentUser = await getMe()
    user.value = currentUser
    return currentUser
  }

  async function login(request: LoginRequest): Promise<void> {
    const tokens = await loginApi(request)
    setTokens(tokens.access_token, tokens.refresh_token)
    try {
      await fetchMe()
    } catch (error) {
      clearAuth()
      throw error
    }
  }

  async function bootstrap(): Promise<void> {
    if (initialized.value) {
      return
    }
    if (bootstrapPromise !== null) {
      return bootstrapPromise
    }

    bootstrapPromise = (async () => {
      try {
        if (getAccessToken() === null) {
          clearAuth()
          return
        }
        await fetchMe()
      } catch {
        clearAuth()
      } finally {
        initialized.value = true
      }
    })().finally(() => {
      bootstrapPromise = null
    })

    return bootstrapPromise
  }

  async function logout(): Promise<void> {
    const accessToken = getAccessToken()
    const refreshToken = getRefreshToken()
    try {
      if (accessToken !== null && refreshToken !== null) {
        await logoutApi({ refresh_token: refreshToken })
      }
    } finally {
      clearAuth()
      initialized.value = true
    }
  }

  return {
    user,
    initialized,
    isAuthenticated,
    isAdmin,
    login,
    fetchMe,
    bootstrap,
    logout,
    clearAuth,
  }
})
