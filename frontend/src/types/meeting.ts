export type MeetingScope = 'hosted' | 'joined' | 'shared' | 'all'

export type MeetingStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'ENDED'

export type MinutesStatus =
  | 'DISABLED'
  | 'WAITING_MEETING_END'
  | 'WAITING_RECORDING'
  | 'WAITING_TRANSCRIPT'
  | 'AI_PROCESSING'
  | 'READY'
  | 'FAILED'

export type MeetingRelation = 'HOST' | 'PARTICIPANT' | 'SHARED' | 'ADMIN'

export interface MeetingHost {
  id: number
  display_name: string
}

export interface MeetingParticipant {
  user_id: number | null
  display_name: string
  is_internal: boolean
}

export interface MeetingPermissions {
  can_view: boolean
  can_edit_minutes: boolean
  can_regenerate: boolean
  can_manage_permissions: boolean
  can_view_ai_versions: boolean
}

export interface MeetingListItem {
  id: number
  subject: string
  meeting_code: string | null
  host: MeetingHost | null
  start_time: string | null
  end_time: string | null
  meeting_status: MeetingStatus
  ai_minutes_enabled: boolean
  minutes_status: MinutesStatus
  my_role: MeetingRelation
}

export interface MeetingListData {
  items: MeetingListItem[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface MeetingDetail {
  id: number
  tencent_meeting_id: string
  meeting_code: string | null
  subject: string
  host: MeetingHost | null
  participants: MeetingParticipant[]
  start_time: string | null
  end_time: string | null
  meeting_status: MeetingStatus
  ai_minutes_enabled: boolean
  minutes_status: MinutesStatus
  permissions: MeetingPermissions
}

export interface MeetingListParams {
  scope?: MeetingScope
  meeting_status?: MeetingStatus
  minutes_status?: MinutesStatus
  keyword?: string
  page?: number
  page_size?: number
}
