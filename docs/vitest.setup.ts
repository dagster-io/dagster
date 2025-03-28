import {vi} from 'vitest';

// Mock React's Suspense for tests
vi.mock('react', async () => {
  const actual = await vi.importActual('react');
  return {
    ...actual,
    Suspense: ({children}: {children: React.ReactNode}) => children,
  };
});

// Set up any global test environment configuration here
