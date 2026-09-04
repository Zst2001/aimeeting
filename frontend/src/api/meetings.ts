import { apiClient } from '@/api/client'
import type { ApiResponse } from '@/types/api'
import type { MeetingDetail, MeetingListData, MeetingListParams } from '@/types/meeting'

export async function getMeetings(params: MeetingListParams): Promise<MeetingListData> {
  const { data } = await apiClient.get<ApiResponse<MeetingListData>>('/api/v1/meetings', { params })
  return data.data
}

export async function getMeetingDetail(meetingId: number): Promise<MeetingDetail> {
  const { data } = await apiClient.get<ApiResponse<MeetingDetail>>(`/api/v1/meetings/${meetingId}`)
  return data.data
}
