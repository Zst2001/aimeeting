<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMeetingDetail } from '@/api/meetings'
import type { MeetingDetail } from '@/types/meeting'
import { formatMeetingTime, meetingStatusLabel, minutesStatusLabel } from '@/utils/meeting'

type DetailState = 'loading' | 'loaded' | 'forbidden' | 'not-found' | 'error'
type ApiError = { response?: { data?: { code?: number; message?: string } } }

const route = useRoute()
const router = useRouter()
const detail = ref<MeetingDetail | null>(null)
const state = ref<DetailState>('loading')
const errorMessage = ref('')
const meetingId = computed(() => Number(route.params.meetingId))

function errorDetails(error: unknown): { code?: number; message?: string } {
  return ((error as ApiError).response?.data ?? {}) as { code?: number; message?: string }
}

async function loadDetail(): Promise<void> {
  if (!Number.isSafeInteger(meetingId.value) || meetingId.value < 1) {
    state.value = 'error'
    errorMessage.value = '会议请求参数无效。'
    return
  }
  state.value = 'loading'
  errorMessage.value = ''
  try {
    detail.value = await getMeetingDetail(meetingId.value)
    state.value = 'loaded'
  } catch (error) {
    const { code, message } = errorDetails(error)
    if (code === 20001) {
      state.value = 'forbidden'
      errorMessage.value = '无会议访问权限'
    } else if (code === 30001) {
      state.value = 'not-found'
      errorMessage.value = '会议不存在'
    } else if (code === 90001) {
      state.value = 'error'
      errorMessage.value = '会议请求参数无效。'
    } else {
      state.value = 'error'
      errorMessage.value = message || '加载会议详情失败，请稍后重试。'
    }
  }
}

function backToMeetings(): void {
  if (window.history.state?.back) {
    router.back()
    return
  }
  void router.replace({ name: 'meetings' })
}

watch(() => route.params.meetingId, () => void loadDetail(), { immediate: true })
</script>

<template>
  <main class="meeting-detail-page">
    <el-button text type="primary" data-testid="back-to-meetings" @click="backToMeetings">← 返回会议列表</el-button>

    <el-skeleton v-if="state === 'loading'" :rows="8" animated />
    <el-result v-else-if="state !== 'loaded'" :icon="state === 'not-found' ? 'warning' : 'error'" :title="errorMessage">
      <template #extra>
        <el-button v-if="state === 'error'" type="primary" @click="loadDetail">重试</el-button>
        <el-button @click="backToMeetings">返回会议列表</el-button>
      </template>
    </el-result>

    <template v-else-if="detail">
      <header class="detail-header">
        <div>
          <h1>{{ detail.subject }}</h1>
          <p v-if="detail.meeting_code">会议号：{{ detail.meeting_code }}</p>
        </div>
        <div class="tags">
          <el-tag>{{ meetingStatusLabel(detail.meeting_status) }}</el-tag>
          <el-tag type="info">{{ minutesStatusLabel(detail.minutes_status) }}</el-tag>
        </div>
      </header>

      <el-card shadow="never" class="detail-card">
        <template #header>基本信息</template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="主持人">{{ detail.host?.display_name ?? '未绑定' }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatMeetingTime(detail.start_time) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatMeetingTime(detail.end_time) }}</el-descriptions-item>
          <el-descriptions-item label="AI纪要">{{ detail.ai_minutes_enabled ? '已开启' : '未开启' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never" class="detail-card">
        <template #header>参会人员</template>
        <el-table :data="detail.participants" data-testid="participants-table">
          <el-table-column prop="display_name" label="姓名" />
          <el-table-column label="类型" width="140">
            <template #default="{ row }"><el-tag :type="row.is_internal ? 'success' : 'info'">{{ row.is_internal ? '内部用户' : '外部参会者' }}</el-tag></template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" class="detail-card permissions-card">
        <template #header>当前权限</template>
        <el-tag :type="detail.permissions.can_view ? 'success' : 'info'">{{ detail.permissions.can_view ? '可查看会议' : '不可查看会议' }}</el-tag>
        <p>权限能力已加载；编辑纪要、重新生成和分享功能将在对应后端 API 交付后开放。</p>
      </el-card>
    </template>
  </main>
</template>

<style scoped>
.meeting-detail-page { min-height: 100vh; padding: 24px; background: #f5f7fa; }
.detail-header { display: flex; justify-content: space-between; gap: 16px; margin: 16px 0; }
.detail-header h1 { margin: 0; }
.detail-header p, .permissions-card p { color: #909399; }
.tags { display: flex; align-items: flex-start; gap: 8px; }
.detail-card { margin-top: 16px; }
@media (max-width: 720px) { .meeting-detail-page { padding: 16px; } .detail-header { flex-direction: column; } }
</style>
