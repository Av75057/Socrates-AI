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
  plugins: [react()],
  server: {
    proxy: apiProxy,
  },
  /** `vite preview` — тот же прокси, что и в dev, иначе fetch('/api/chat') падает с NetworkError */
  preview: {
    proxy: apiProxy,
  },
});
