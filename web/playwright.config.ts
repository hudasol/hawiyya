import { defineConfig, devices } from "@playwright/test";

// End to end tests run against the static build (no backend needed).
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:4791", ...devices["Desktop Chrome"] },
  webServer: {
    command: "npx vite preview --port 4791 --strictPort",
    url: "http://localhost:4791",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
