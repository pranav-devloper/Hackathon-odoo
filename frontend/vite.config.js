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
      "/org": "http://localhost:8000",
      "/assets": "http://localhost:8000",
      "/dashboard": "http://localhost:8000",
      "/allocations": "http://localhost:8000",
      "/transfers": "http://localhost:8000",
      "/notifications": "http://localhost:8000",
      "/docs": "http://localhost:8000",
      "/openapi.json": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
    // Serve built JS/CSS from /static so they don't collide with the
    // FastAPI /assets/{asset_id} API route when FastAPI serves the SPA.
    assetsDir: "static",
  },
});
