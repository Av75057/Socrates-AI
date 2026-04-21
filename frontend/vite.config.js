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
    /**
     * 0.0.0.0 — доступ по LAN (не используйте CLI `--host 127.0.0.1`, иначе с других устройств не откроется).
     */
    host: "0.0.0.0",
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
    host: "0.0.0.0",
    port: 4173,
    allowedHosts: true,
    proxy: apiProxy,
  },
});
