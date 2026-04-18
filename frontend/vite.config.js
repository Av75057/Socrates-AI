import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxy = {
  "/api": {
    target: "http://127.0.0.1:8000",
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  /** Явно SPA: dev/preview отдают index.html на любые пути (React Router). */
  appType: "spa",
  plugins: [react()],
  server: {
    /** Слушать все интерфейсы — LAN и проброс с роутера на этот ПК */
    host: true,
    port: 5173,
    /**
     * Иначе Vite отвечает 403 для Host = домен/DDNS/вход с интернета по имени, не по IP.
     * @see https://vite.dev/config/server-options.html#server-allowedhosts
     */
    allowedHosts: true,
    proxy: apiProxy,
  },
  /** `vite preview` — тот же прокси, что и в dev, иначе fetch('/api/chat') падает с NetworkError */
  preview: {
    host: true,
    port: 4173,
    allowedHosts: true,
    proxy: apiProxy,
  },
});
