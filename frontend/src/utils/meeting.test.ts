import { describe, expect, it } from 'vitest'

import {
  availableMeetingScopes,
  formatMeetingTime,
  meetingListQuery,
  meetingRelationLabel,
  meetingStatusLabel,
  minutesStatusLabel,
  normalizeMeetingListQuery,
} from '@/utils/meeting'

describe('meeting list route state', () => {
  it('uses hosted, page 1 and page size 20 as safe defaults', () => {
    expect(normalizeMeetingListQuery({})).toEqual({
      scope: 'hosted',
      meetingStatus: undefined,
      minutesStatus: undefined,
      keyword: '',
      page: 1,
      pageSize: 20,
    })
  })

  it('restores every supported filter from a URL query', () => {
    expect(
      normalizeMeetingListQuery({
        scope: 'joined',
        meeting_status: 'ENDED',
        minutes_status: 'READY',
        keyword: ' alpha ',
        page: '2',
        page_size: '50',
      }),
    ).toEqual({
      scope: 'joined',
      meetingStatus: 'ENDED',
      minutesStatus: 'READY',
      keyword: 'alpha',
      page: 2,
      pageSize: 50,
    })
  })

  it('normalizes invalid scope, enums and pagination without requesting an invalid API query', () => {
    expect(
      normalizeMeetingListQuery({
        scope: 'visible',
        meeting_status: 'PAUSED',
        minutes_status: 'UNKNOWN',
        page: '0',
        page_size: '999',
      }),
    ).toMatchObject({ scope: 'hosted', page: 1, pageSize: 20 })
  })

  it('normalizes non-numeric page values and repeated query values', () => {
    expect(normalizeMeetingListQuery({ scope: ['shared', 'all'], page: 'abc', page_size: '100' })).toMatchObject({
      scope: 'shared',
      page: 1,
      pageSize: 100,
    })
  })

  it('serializes canonical query values for URL synchronization', () => {
    expect(
      meetingListQuery({
        scope: 'shared',
        meetingStatus: undefined,
        minutesStatus: 'READY',
        keyword: 'release',
        page: 3,
        pageSize: 50,
      }),
    ).toEqual({
      scope: 'shared',
      meeting_status: undefined,
      minutes_status: 'READY',
      keyword: 'release',
      page: '3',
      page_size: '50',
    })
  })
})

describe('meeting presentation helpers', () => {
  it('keeps the all scope out of the regular user UI', () => {
    expect(availableMeetingScopes(false)).toEqual(['hosted', 'joined', 'shared'])
  })

  it('shows the all scope to an administrator', () => {
    expect(availableMeetingScopes(true)).toEqual(['hosted', 'joined', 'shared', 'all'])
  })

  it('maps all backend meeting and minutes statuses to Chinese labels', () => {
    expect(meetingStatusLabel('SCHEDULED')).toBe('待开始')
    expect(meetingStatusLabel('IN_PROGRESS')).toBe('进行中')
    expect(meetingStatusLabel('ENDED')).toBe('已结束')
    expect(minutesStatusLabel('DISABLED')).toBe('未开启')
    expect(minutesStatusLabel('WAITING_MEETING_END')).toBe('等待会议结束')
    expect(minutesStatusLabel('WAITING_RECORDING')).toBe('等待录制')
    expect(minutesStatusLabel('WAITING_TRANSCRIPT')).toBe('等待转写')
    expect(minutesStatusLabel('AI_PROCESSING')).toBe('生成中')
    expect(minutesStatusLabel('READY')).toBe('已生成')
    expect(minutesStatusLabel('FAILED')).toBe('生成失败')
  })

  it('maps the backend relation rather than inferring it in the browser', () => {
    expect(meetingRelationLabel('HOST')).toBe('主持人')
    expect(meetingRelationLabel('PARTICIPANT')).toBe('参会者')
    expect(meetingRelationLabel('SHARED')).toBe('已授权')
    expect(meetingRelationLabel('ADMIN')).toBe('管理员')
  })

  it('renders nullable meeting time with a non-breaking fallback', () => {
    expect(formatMeetingTime(null)).toBe('未设置')
  })
})
