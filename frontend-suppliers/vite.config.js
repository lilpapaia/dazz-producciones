import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'DAZZ Suppliers',
        short_name: 'DAZZ Suppliers',
        description: 'Supplier portal for DAZZ Group',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: '#09090b',
        theme_color: '#f59e0b',
        orientation: 'portrait-primary',
        categories: ['business', 'productivity'],
        icons: [
          { src: '/favicon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/dazz-producciones-production\.up\.railway\.app\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 10,
              expiration: { maxEntries: 50, maxAgeSeconds: 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
        navigateFallbackDenylist: [/^\/api\//],
      },
      devOptions: { enabled: true, type: 'module', navigateFallback: 'index.html' },
    }),
  ],
  server: { port: 5174 },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
})
