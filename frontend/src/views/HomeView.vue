<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getBackendHealth } from '@/api/client'

const backendStatus = ref<'checking' | 'ok' | 'error'>('checking')

async function refreshBackendStatus(): Promise<void> {
  backendStatus.value = 'checking'
  try {
    const health = await getBackendHealth()
    backendStatus.value = health.status === 'ok' ? 'ok' : 'error'
  } catch {
    backendStatus.value = 'error'
  }
}

onMounted(refreshBackendStatus)
</script>

<template>
  <main class="home-page">
    <el-card class="status-card" shadow="never">
      <h1>AI 智能会议纪要系统</h1>
      <p>Phase 1 Task 1：基础工程与健康检查。</p>
      <el-divider />
      <div class="status-row">
        <span>Backend Status</span>
        <el-tag v-if="backendStatus === 'ok'" type="success">正常</el-tag>
        <el-tag v-else-if="backendStatus === 'checking'" type="info">检查中</el-tag>
        <el-tag v-else type="danger">不可用</el-tag>
        <el-button text type="primary" @click="refreshBackendStatus">刷新</el-button>
      </div>
    </el-card>
  </main>
</template>

<style scoped>
.home-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
  background: #f5f7fa;
}

.status-card {
  width: min(100%, 560px);
}

.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
