<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMeetings } from '@/api/meetings'
import { useAuthStore } from '@/stores/auth'
import type { MeetingListData, MeetingScope, MeetingStatus, MinutesStatus } from '@/types/meeting'
import {
  formatMeetingTime,
  availableMeetingScopes,
  meetingListQuery,
  meetingRelationLabel,
  meetingStatusLabel,
  minutesStatusLabel,
  normalizeMeetingListQuery,
} from '@/utils/meeting'

type ApiError = { response?: { data?: { code?: number; message?: string } } }

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const state = reactive({
  scope: 'hosted' as MeetingScope,
  meetingStatus: undefined as MeetingStatus | undefined,
  minutesStatus: undefined as MinutesStatus | undefined,
  keyword: '',
  page: 1,
  pageSize: 20,
})
const keywordInput = ref('')
const listData = ref<MeetingListData | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const noticeMessage = ref('')
let activeRequest = 0

const availableScopes = computed(() => {
  const labels: Record<MeetingScope, string> = {
    hosted: '我主持的',
    joined: '我参加的',
    shared: '分享给我的',
    all: '全部',
  }
  return availableMeetingScopes(authStore.isAdmin).map((value) => ({ value, label: labels[value] }))
})

function routeMatchesState(): boolean {
  return router.resolve({ name: 'meetings', query: meetingListQuery(state) }).fullPath === route.fullPath
}

async function replaceRoute(): Promise<void> {
  await router.replace({ name: 'meetings', query: meetingListQuery(state) })
}

function errorDetails(error: unknown): { code?: number; message?: string } {
  return ((error as ApiError).response?.data ?? {}) as { code?: number; message?: string }
}

async function loadMeetings(): Promise<void> {
  const request = ++activeRequest
  loading.value = true
  errorMessage.value = ''
  try {
    listData.value = await getMeetings({
      scope: state.scope,
      meeting_status: state.meetingStatus,
      minutes_status: state.minutesStatus,
      keyword: state.keyword || undefined,
      page: state.page,
      page_size: state.pageSize,
    })
  } catch (error) {
    if (request !== activeRequest) {
      return
    }
    const { code, message } = errorDetails(error)
    if (code === 20004) {
      noticeMessage.value = '权限不足，已切换到我主持的会议。'
      state.scope = 'hosted'
      state.page = 1
      await replaceRoute()
      return
    }
    if (code === 90001) {
      noticeMessage.value = '地址中的筛选参数无效，已恢复为安全默认值。'
      Object.assign(state, {
        scope: 'hosted',
        meetingStatus: undefined,
        minutesStatus: undefined,
        keyword: '',
        page: 1,
        pageSize: 20,
      })
      keywordInput.value = ''
      await replaceRoute()
      return
    }
    errorMessage.value = message || '加载会议列表失败，请稍后重试。'
  } finally {
    if (request === activeRequest) {
      loading.value = false
    }
  }
}

function syncAndLoad(): void {
  void replaceRoute()
}

function changeScope(scope: MeetingScope): void {
  state.scope = scope
  state.page = 1
  syncAndLoad()
}

function changeMeetingStatus(status: MeetingStatus | undefined): void {
  state.meetingStatus = status
  state.page = 1
  syncAndLoad()
}

function changeMinutesStatus(status: MinutesStatus | undefined): void {
  state.minutesStatus = status
  state.page = 1
  syncAndLoad()
}

function search(): void {
  state.keyword = keywordInput.value.trim()
  state.page = 1
  syncAndLoad()
}

function resetFilters(): void {
  state.meetingStatus = undefined
  state.minutesStatus = undefined
  state.keyword = ''
  keywordInput.value = ''
  state.page = 1
  syncAndLoad()
}

function changePage(page: number): void {
  state.page = page
  syncAndLoad()
}

function changePageSize(pageSize: number): void {
  state.pageSize = pageSize
  state.page = 1
  syncAndLoad()
}

async function logout(): Promise<void> {
  await authStore.logout()
  await router.replace({ name: 'login' })
}

watch(
  () => route.fullPath,
  () => {
    const restored = normalizeMeetingListQuery(route.query)
    Object.assign(state, restored)
    keywordInput.value = restored.keyword
    if (!routeMatchesState()) {
      void replaceRoute()
      return
    }
    void loadMeetings()
  },
  { immediate: true },
)
</script>

<template>
  <main class="meetings-page">
    <header class="page-header">
      <div>
        <h1>会议</h1>
        <p>查看与你相关的会议基础信息。</p>
      </div>
      <div class="account-actions">
        <span>{{ authStore.user?.display_name }}</span>
        <el-button text type="danger" data-testid="logout" @click="logout">退出登录</el-button>
      </div>
    </header>

    <el-alert v-if="noticeMessage" :title="noticeMessage" type="warning" :closable="true" @close="noticeMessage = ''" />
    <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false">
      <template #default>
        <el-button text type="primary" data-testid="retry-list" @click="loadMeetings">重试</el-button>
      </template>
    </el-alert>

    <el-card shadow="never">
      <el-tabs :model-value="state.scope" data-testid="scope-tabs" @tab-change="changeScope($event as MeetingScope)">
        <el-tab-pane v-for="scopeOption in availableScopes" :key="scopeOption.value" :name="scopeOption.value" :label="scopeOption.label" />
      </el-tabs>

      <div class="filters">
        <el-select
          :model-value="state.meetingStatus"
          placeholder="会议状态"
          clearable
          data-testid="meeting-status-filter"
          @update:model-value="changeMeetingStatus"
        >
          <el-option label="待开始" value="SCHEDULED" />
          <el-option label="进行中" value="IN_PROGRESS" />
          <el-option label="已结束" value="ENDED" />
        </el-select>
        <el-select
          :model-value="state.minutesStatus"
          placeholder="AI纪要状态"
          clearable
          data-testid="minutes-status-filter"
          @update:model-value="changeMinutesStatus"
        >
          <el-option label="未开启" value="DISABLED" />
          <el-option label="等待会议结束" value="WAITING_MEETING_END" />
          <el-option label="等待录制" value="WAITING_RECORDING" />
          <el-option label="等待转写" value="WAITING_TRANSCRIPT" />
          <el-option label="生成中" value="AI_PROCESSING" />
          <el-option label="已生成" value="READY" />
          <el-option label="生成失败" value="FAILED" />
        </el-select>
        <el-input v-model="keywordInput" placeholder="搜索会议主题或会议号" clearable data-testid="keyword-input" @keyup.enter="search" />
        <el-button type="primary" data-testid="keyword-search" @click="search">搜索</el-button>
        <el-button data-testid="reset-filters" @click="resetFilters">重置</el-button>
      </div>

      <el-table v-if="listData?.items.length || loading" v-loading="loading" :data="listData?.items ?? []" data-testid="meeting-table">
        <el-table-column prop="subject" label="会议主题" min-width="180">
          <template #default="{ row }">
            <strong>{{ row.subject }}</strong>
            <div v-if="row.meeting_code" class="secondary">会议号：{{ row.meeting_code }}</div>
          </template>
        </el-table-column>
        <el-table-column label="主持人" min-width="120">
          <template #default="{ row }">{{ row.host?.display_name ?? '未绑定' }}</template>
        </el-table-column>
        <el-table-column label="开始时间" min-width="170">
          <template #default="{ row }">{{ formatMeetingTime(row.start_time) }}</template>
        </el-table-column>
        <el-table-column label="会议状态" min-width="105">
          <template #default="{ row }"><el-tag>{{ meetingStatusLabel(row.meeting_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="AI纪要状态" min-width="130">
          <template #default="{ row }"><el-tag type="info">{{ minutesStatusLabel(row.minutes_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="我的角色" min-width="100">
          <template #default="{ row }"><el-tag type="success">{{ meetingRelationLabel(row.my_role) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push({ name: 'meeting-detail', params: { meetingId: row.id } })">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else-if="!loading && !errorMessage" description="当前没有符合条件的会议" data-testid="meeting-empty" />

      <div v-if="listData" class="pagination-row">
        <el-pagination
          :current-page="listData.page"
          :page-size="listData.page_size"
          :page-sizes="[20, 50, 100]"
          :total="listData.total"
          layout="total, sizes, prev, pager, next"
          @current-change="changePage"
          @size-change="changePageSize"
        />
      </div>
    </el-card>
  </main>
</template>

<style scoped>
.meetings-page { min-height: 100vh; padding: 24px; background: #f5f7fa; }
.page-header, .account-actions, .filters, .pagination-row { display: flex; align-items: center; }
.page-header { justify-content: space-between; margin-bottom: 20px; }
.page-header h1 { margin: 0; }
.page-header p, .secondary { color: #909399; }
.account-actions { gap: 12px; }
.filters { flex-wrap: wrap; gap: 12px; margin: 16px 0; }
.filters :deep(.el-select) { width: 160px; }
.filters :deep(.el-input) { width: 260px; }
.pagination-row { justify-content: flex-end; margin-top: 20px; }
.el-alert { margin-bottom: 16px; }
@media (max-width: 720px) { .meetings-page { padding: 16px; } .page-header { align-items: flex-start; gap: 12px; flex-direction: column; } }
</style>
