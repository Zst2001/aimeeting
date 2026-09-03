import { apiClient, authClient } from '@/api/client'
import type { ApiResponse } from '@/types/api'
import type { LoginData, LoginRequest, LogoutRequest, RefreshData, User } from '@/types/auth'

export async function login(request: LoginRequest): Promise<LoginData> {
  const { data } = await apiClient.post<ApiResponse<LoginData>>('/api/v1/auth/login', request)
  return data.data
}

export async function refresh(refreshToken: string): Promise<RefreshData> {
  const { data } = await authClient.post<ApiResponse<RefreshData>>('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  })
  return data.data
}

export async function logout(request: LogoutRequest): Promise<void> {
  await apiClient.post('/api/v1/auth/logout', request)
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<ApiResponse<User>>('/api/v1/me')
  return data.data
}
