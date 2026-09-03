<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getBackendHealth } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const backendStatus = ref<'checking' | 'ok' | 'error'>('checking')
const loggingOut = ref(false)
const authStore = useAuthStore()
const router = useRouter()
const currentUser = computed(() => authStore.user)

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

async function logout(): Promise<void> {
  loggingOut.value = true
  try {
    await authStore.logout()
  } finally {
    loggingOut.value = false
    await router.replace({ name: 'login' })
  }
}
</script>

<template>
  <main class="home-page">
    <el-card class="status-card" shadow="never">
      <h1>AI 智能会议纪要系统</h1>
      <p>欢迎，{{ currentUser?.display_name }}</p>
      <dl class="user-details">
        <div><dt>用户名</dt><dd>{{ currentUser?.username }}</dd></div>
        <div><dt>角色</dt><dd>{{ currentUser?.role }}</dd></div>
      </dl>
      <el-button type="danger" plain :loading="loggingOut" @click="logout">退出登录</el-button>
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

.user-details {
  display: grid;
  gap: 8px;
  margin: 20px 0;
}

.user-details div {
  display: flex;
  gap: 12px;
}

dt {
  color: #909399;
}

dd {
  margin: 0;
}
</style>
