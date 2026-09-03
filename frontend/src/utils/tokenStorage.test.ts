import { beforeEach, describe, expect, it } from 'vitest'

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/tokenStorage'

describe('tokenStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('stores and clears an access and refresh token as a pair', () => {
    setTokens('access-a', 'refresh-a')

    expect(getAccessToken()).toBe('access-a')
    expect(getRefreshToken()).toBe('refresh-a')

    clearTokens()

    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })
})
