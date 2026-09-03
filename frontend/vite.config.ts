import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

const backendProxyTarget = process.env.VITE_BACKEND_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    proxy: {
      '/health': { target: backendProxyTarget },
      '/ready': { target: backendProxyTarget },
      '/api': { target: backendProxyTarget },
    },
  },
  test: {
    environment: 'jsdom',
    clearMocks: true,
  },
})
