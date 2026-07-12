import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /auth (and the API surface) to the FastAPI backend on
// :8000 so the SPA can call the API same-origin (no CORS, no env config).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/docs": "http://localhost:8000",
      "/openapi.json": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
  },
});
