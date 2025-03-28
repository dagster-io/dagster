import {defineConfig} from 'vitest/config';
import {resolve} from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./vitest.setup.ts'],
    alias: {
      '@theme/CodeBlock': resolve(__dirname, './vitest.mocks.ts'),
      '../code-examples-content': resolve(__dirname, './vitest.mocks.ts'),
    },
  },
});
