import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/ui/',   // new
  plugins: [react()],
  server: {
    port: 4174,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
