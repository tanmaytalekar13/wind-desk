import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  css: { postcss: {} },
  server: { proxy: { "/api": process.env.VITE_PROXY ?? "http://localhost:8000" } },
});
