import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    // Prefer .ts/.tsx over .js/.jsx so api.ts is found before api.js
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
