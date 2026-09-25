import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const backend = process.env.BACKEND_URL || "http://127.0.0.1:8001";

export default defineConfig(({ command }) => ({
  plugins: [react(), tailwindcss()],
  base:
    command === "build" ? `${process.env.APP_BASE_PATH || ""}/static/` : "/",
  build: { outDir: "../src/static", emptyOutDir: true, sourcemap: false },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: backend,
        changeOrigin: true,
        configure(proxy) {
          proxy.on("proxyReq", (outgoing, incoming) => {
            // Preserve foreign origins so backend CSRF checks still reject them.
            if (
              ["http://127.0.0.1:5173", "http://localhost:5173"].includes(
                incoming.headers.origin || "",
              )
            ) {
              outgoing.setHeader("origin", new URL(backend).origin);
            }
          });
        },
      },
    },
  },
}));
