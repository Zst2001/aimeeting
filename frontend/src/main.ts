import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'

import App from './App.vue'
import { setAuthFailureHandler } from './api/client'
import { router } from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia).use(router).use(ElementPlus)

setAuthFailureHandler(() => {
  const authStore = useAuthStore(pinia)
  authStore.clearAuth()
  authStore.initialized = true
  if (router.currentRoute.value.name !== 'login') {
    void router.replace({ name: 'login' })
  }
})

async function initializeApplication(): Promise<void> {
  await useAuthStore(pinia).bootstrap()
  app.mount('#app')
}

void initializeApplication()
