import axios, { AxiosError, AxiosHeaders, type InternalAxiosRequestConfig } from 'axios'

import type { ApiResponse } from '@/types/api'
import type { RefreshData } from '@/types/auth'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/tokenStorage'

export const apiClient = axios.create({
  baseURL: '',
  timeout: 5_000,
})

// Refresh must not use the intercepted client, otherwise an expired refresh
// token could recursively trigger another refresh attempt.
export const authClient = axios.create({
  baseURL: '',
  timeout: 5_000,
})

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean
}

type AuthFailureHandler = () => void

let refreshPromise: Promise<string> | null = null
let authFailureHandler: AuthFailureHandler = clearTokens

const refreshExcludedPaths = ['/api/v1/auth/login', '/api/v1/auth/refresh']
const authPaths = [...refreshExcludedPaths, '/api/v1/auth/logout']

function isPathMatch(url: string | undefined, paths: string[]): boolean {
  return Boolean(url && paths.some((path) => url.includes(path)))
}

export function setAuthFailureHandler(handler: AuthFailureHandler): void {
  authFailureHandler = handler
}

export function resetAuthClientStateForTests(): void {
  refreshPromise = null
  authFailureHandler = clearTokens
}

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise === null) {
    const refreshToken = getRefreshToken()
    refreshPromise = refreshToken
      ? authClient
          .post<ApiResponse<RefreshData>>('/api/v1/auth/refresh', { refresh_token: refreshToken })
          .then(({ data }) => {
            if (data.code !== 0) {
              throw new Error(data.message)
            }
            setTokens(data.data.access_token, data.data.refresh_token)
            return data.data.access_token
          })
      : Promise.reject(new Error('Refresh token is unavailable'))

    refreshPromise = refreshPromise.finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

apiClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken()
  if (accessToken && !isPathMatch(config.url, refreshExcludedPaths)) {
    const headers = AxiosHeaders.from(config.headers)
    headers.set('Authorization', `Bearer ${accessToken}`)
    config.headers = headers
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as RetriableRequestConfig | undefined
    const isUnauthorized = error.response?.status === 401

    if (
      !isUnauthorized ||
      originalRequest === undefined ||
      originalRequest._retry === true ||
      isPathMatch(originalRequest.url, authPaths)
    ) {
      return Promise.reject(error)
    }

    originalRequest._retry = true
    try {
      const newAccessToken = await refreshAccessToken()
      const headers = AxiosHeaders.from(originalRequest.headers)
      headers.set('Authorization', `Bearer ${newAccessToken}`)
      originalRequest.headers = headers
      return apiClient.request(originalRequest)
    } catch (refreshError) {
      authFailureHandler()
      return Promise.reject(refreshError)
    }
  },
)

export type HealthResponse = {
  status: 'ok'
}

export async function getBackendHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}
