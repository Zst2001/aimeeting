import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  apiClient,
  authClient,
  resetAuthClientStateForTests,
  setAuthFailureHandler,
} from '@/api/client'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/tokenStorage'

function authorizationHeader(headers: unknown): string | undefined {
  if (headers && typeof headers === 'object' && 'Authorization' in headers) {
    const value = (headers as Record<string, unknown>).Authorization
    return typeof value === 'string' ? value : undefined
  }
  return undefined
}

describe('api client authentication interceptors', () => {
  let apiMock: MockAdapter
  let authMock: MockAdapter

  beforeEach(() => {
    localStorage.clear()
    resetAuthClientStateForTests()
    apiMock = new MockAdapter(apiClient)
    authMock = new MockAdapter(authClient)
  })

  afterEach(() => {
    apiMock.restore()
    authMock.restore()
    clearTokens()
  })

  it('adds a bearer token to protected requests', async () => {
    setTokens('access-a', 'refresh-a')
    apiMock.onGet('/protected').reply((config) => {
      expect(authorizationHeader(config.headers)).toBe('Bearer access-a')
      return [200, { ok: true }]
    })

    await expect(apiClient.get('/protected')).resolves.toMatchObject({ status: 200 })
  })

  it('refreshes once, stores both rotated tokens, and retries the original request', async () => {
    setTokens('access-old', 'refresh-old')
    authMock.onPost('/api/v1/auth/refresh').reply(200, {
      code: 0,
      message: 'ok',
      data: {
        access_token: 'access-new',
        refresh_token: 'refresh-new',
        token_type: 'bearer',
        expires_in: 1800,
      },
      request_id: 'req_refresh',
    })
    apiMock.onGet('/protected').reply((config) => {
      return authorizationHeader(config.headers) === 'Bearer access-new' ? [200, { ok: true }] : [401]
    })

    await expect(apiClient.get('/protected')).resolves.toMatchObject({ status: 200 })

    expect(authMock.history.post).toHaveLength(1)
    expect(getAccessToken()).toBe('access-new')
    expect(getRefreshToken()).toBe('refresh-new')
  })

  it('uses one refresh promise for three concurrent 401 responses and retries all requests', async () => {
    setTokens('access-old', 'refresh-old')
    authMock.onPost('/api/v1/auth/refresh').reply(200, {
      code: 0,
      message: 'ok',
      data: {
        access_token: 'access-new',
        refresh_token: 'refresh-new',
        token_type: 'bearer',
        expires_in: 1800,
      },
      request_id: 'req_refresh',
    })
    for (const path of ['/protected/a', '/protected/b', '/protected/c']) {
      apiMock.onGet(path).reply((config) => {
        return authorizationHeader(config.headers) === 'Bearer access-new' ? [200, { path }] : [401]
      })
    }

    const responses = await Promise.all([
      apiClient.get('/protected/a'),
      apiClient.get('/protected/b'),
      apiClient.get('/protected/c'),
    ])

    expect(authMock.history.post).toHaveLength(1)
    expect(responses.map((response) => response.status)).toEqual([200, 200, 200])
    expect(responses.map((response) => response.data.path)).toEqual(['/protected/a', '/protected/b', '/protected/c'])
  })

  it('clears the local session once refresh ultimately fails', async () => {
    setTokens('access-old', 'refresh-old')
    const handleFailure = vi.fn(clearTokens)
    setAuthFailureHandler(handleFailure)
    authMock.onPost('/api/v1/auth/refresh').reply(401, { code: 10004, message: 'Refresh Token 无效' })
    apiMock.onGet('/protected').reply(401)

    await expect(apiClient.get('/protected')).rejects.toBeDefined()

    expect(handleFailure).toHaveBeenCalledOnce()
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
    expect(authMock.history.post).toHaveLength(1)
  })
})
