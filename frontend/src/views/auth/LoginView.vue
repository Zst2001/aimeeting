<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import type { ApiResponse } from '@/types/api'
import { getSafeRedirectPath } from '@/utils/navigation'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')
const form = reactive({ username: '', password: '' })

const rules: FormRules<typeof form> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function resolveErrorMessage(error: unknown): string {
  const response = (error as { response?: { data?: ApiResponse<unknown> } }).response
  const code = response?.data?.code
  if (code === 10001) {
    return '用户名或密码错误'
  }
  if (code === 10005) {
    return '当前账户已被禁用，请联系管理员'
  }
  return '登录失败，请稍后重试'
}

async function submit(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    await authStore.login({ username: form.username, password: form.password })
    const redirect = getSafeRedirectPath(route.query.redirect)
    await router.replace(redirect ?? { name: 'meetings' })
  } catch (error) {
    errorMessage.value = resolveErrorMessage(error)
    ElMessage.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <el-card class="login-card" shadow="never">
      <header>
        <h1>AI 智能会议纪要系统</h1>
        <p>请使用公司账号登录</p>
      </header>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" :closable="false" show-icon />

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" autocomplete="username" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="login-button">
          登录
        </el-button>
      </el-form>
    </el-card>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
  background: #f5f7fa;
}

.login-card {
  width: min(100%, 420px);
}

header {
  margin-bottom: 24px;
}

h1 {
  margin: 0;
  font-size: 24px;
}

p {
  margin: 8px 0 0;
  color: #909399;
}

.el-alert {
  margin-bottom: 16px;
}

.login-button {
  width: 100%;
}
</style>
