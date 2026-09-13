import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 90_000,
  workers: 1,
  use: {
    baseURL: process.env.AUTH_SITE_URL || 'http://localhost:3000',
    screenshot: 'off',
    trace: 'off',
  },
});
