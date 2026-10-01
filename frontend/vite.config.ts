import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The browser calls /api/*; Vite forwards it to the backend with the prefix removed.
const backend = process.env.API_PROXY_TARGET ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: backend, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') } },
  },
  preview: {
    port: 5173,
    proxy: { '/api': { target: backend, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') } },
  },
});
