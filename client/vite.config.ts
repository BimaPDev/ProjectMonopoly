import * as path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.VITE_BACKEND_URL || 'http://localhost:8080';
  console.log("DEBUG_TARGET_START|" + target + "|DEBUG_TARGET_END");

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      proxy: {
        '/api': {
          target: target,
          changeOrigin: true,
          secure: false,
        },
        '/followers': {
          target: target,
          changeOrigin: true,
          secure: false,
        }
      }
    },
    preview: {
      proxy: {
        '/api': {
          target: target,
          changeOrigin: true,
          secure: false,
        },
        '/followers': {
          target: target,
          changeOrigin: true,
          secure: false,
        }
      }
    }
  };
});
