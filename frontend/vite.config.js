import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // Shares the one root .env with the backend instead of needing a
  // separate frontend/.env.
  envDir: '../',
  server: {
    proxy: {
      '/uploads': 'http://localhost:8000',
    },
  },
})
