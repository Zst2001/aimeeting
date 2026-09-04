import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { getMeetingDetail, getMeetings } from '@/api/meetings'
import { apiClient } from '@/api/client'

describe('meeting API client', () => {
  let mock: MockAdapter

  beforeEach(() => {
    mock = new MockAdapter(apiClient)
  })

  afterEach(() => {
    mock.restore()
  })

  it('serializes only the Task 3 list query contract', async () => {
    mock.onGet('/api/v1/meetings').reply((config) => {
      expect(config.params).toEqual({
        scope: 'joined',
        meeting_status: 'ENDED',
        minutes_status: 'READY',
        keyword: 'alpha',
        page: 2,
        page_size: 50,
      })
      return [200, { code: 0, message: 'ok', data: { items: [], page: 2, page_size: 50, total: 0, total_pages: 0 }, request_id: 'req' }]
    })

    await expect(
      getMeetings({ scope: 'joined', meeting_status: 'ENDED', minutes_status: 'READY', keyword: 'alpha', page: 2, page_size: 50 }),
    ).resolves.toMatchObject({ page: 2, page_size: 50 })
  })

  it('uses the fixed read-only detail endpoint', async () => {
    mock.onGet('/api/v1/meetings/42').reply(200, {
      code: 0,
      message: 'ok',
      data: { id: 42, subject: '测试会议' },
      request_id: 'req',
    })

    await expect(getMeetingDetail(42)).resolves.toMatchObject({ id: 42, subject: '测试会议' })
  })
})
