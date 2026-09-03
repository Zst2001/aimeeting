export type UserRole = 'USER' | 'ADMIN'
export type UserStatus = 'ACTIVE' | 'DISABLED'

export interface User {
  id: number
  username: string
  employee_no: string | null
  display_name: string
  email: string | null
  role: UserRole
  status: UserStatus
}

export interface LoginUser {
  id: number
  username: string
  display_name: string
  role: UserRole
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface LoginData extends TokenPair {
  user: LoginUser
}

export interface RefreshRequest {
  refresh_token: string
}

export type RefreshData = TokenPair

export interface LogoutRequest {
  refresh_token: string
}
