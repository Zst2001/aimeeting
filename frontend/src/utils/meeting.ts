import type { LocationQuery, LocationQueryRaw } from 'vue-router'

import type { MeetingRelation, MeetingScope, MeetingStatus, MinutesStatus } from '@/types/meeting'

export const meetingScopes: MeetingScope[] = ['hosted', 'joined', 'shared', 'all']
export const meetingStatuses: MeetingStatus[] = ['SCHEDULED', 'IN_PROGRESS', 'ENDED']
export const minutesStatuses: MinutesStatus[] = [
  'DISABLED',
  'WAITING_MEETING_END',
  'WAITING_RECORDING',
  'WAITING_TRANSCRIPT',
  'AI_PROCESSING',
  'READY',
  'FAILED',
]

export function availableMeetingScopes(isAdmin: boolean): MeetingScope[] {
  return isAdmin ? ['hosted', 'joined', 'shared', 'all'] : ['hosted', 'joined', 'shared']
}

export interface MeetingListRouteState {
  scope: MeetingScope
  meetingStatus?: MeetingStatus
  minutesStatus?: MinutesStatus
  keyword: string
  page: number
  pageSize: number
}

const defaultPageSize = 20
const permittedPageSizes = [20, 50, 100]

function firstQueryValue(value: LocationQuery[string]): string | undefined {
  return Array.isArray(value) ? value[0] ?? undefined : value ?? undefined
}

function isOneOf<T extends string>(value: string | undefined, values: readonly T[]): value is T {
  return value !== undefined && values.includes(value as T)
}

function positiveInteger(value: string | undefined, fallback: number): number {
  if (value === undefined || !/^\d+$/.test(value)) {
    return fallback
  }
  const parsed = Number(value)
  return parsed >= 1 && Number.isSafeInteger(parsed) ? parsed : fallback
}

export function normalizeMeetingListQuery(query: LocationQuery): MeetingListRouteState {
  const scope = firstQueryValue(query.scope)
  const meetingStatus = firstQueryValue(query.meeting_status)
  const minutesStatus = firstQueryValue(query.minutes_status)
  const keyword = firstQueryValue(query.keyword)?.trim() ?? ''
  const requestedPageSize = positiveInteger(firstQueryValue(query.page_size), defaultPageSize)

  return {
    scope: isOneOf(scope, meetingScopes) ? scope : 'hosted',
    meetingStatus: isOneOf(meetingStatus, meetingStatuses) ? meetingStatus : undefined,
    minutesStatus: isOneOf(minutesStatus, minutesStatuses) ? minutesStatus : undefined,
    keyword,
    page: positiveInteger(firstQueryValue(query.page), 1),
    pageSize: permittedPageSizes.includes(requestedPageSize) ? requestedPageSize : defaultPageSize,
  }
}

export function meetingListQuery(state: MeetingListRouteState): LocationQueryRaw {
  return {
    scope: state.scope,
    meeting_status: state.meetingStatus,
    minutes_status: state.minutesStatus,
    keyword: state.keyword || undefined,
    page: String(state.page),
    page_size: String(state.pageSize),
  }
}

export function meetingStatusLabel(status: MeetingStatus): string {
  return {
    SCHEDULED: '待开始',
    IN_PROGRESS: '进行中',
    ENDED: '已结束',
  }[status]
}

export function minutesStatusLabel(status: MinutesStatus): string {
  return {
    DISABLED: '未开启',
    WAITING_MEETING_END: '等待会议结束',
    WAITING_RECORDING: '等待录制',
    WAITING_TRANSCRIPT: '等待转写',
    AI_PROCESSING: '生成中',
    READY: '已生成',
    FAILED: '生成失败',
  }[status]
}

export function meetingRelationLabel(relation: MeetingRelation): string {
  return {
    HOST: '主持人',
    PARTICIPANT: '参会者',
    SHARED: '已授权',
    ADMIN: '管理员',
  }[relation]
}

export function formatMeetingTime(value: string | null): string {
  if (!value) {
    return '未设置'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    hour12: false,
  }).format(date)
}
