// Browser APIs that are not available in worker contexts
export const UNSAFE_BROWSER_APIS = new Set([
  // Global objects
  'window',
  'document',
  'navigator',

  // DOM-related globals
  'Element',
  'HTMLElement',
  'Node',

  // Browser storage
  'localStorage',
  'sessionStorage',

  // Location and history
  'location',
  'history',

  // Alert and other UI functions
  'alert',
  'confirm',
  'prompt',

  // Animation and timing
  'requestAnimationFrame',
  'cancelAnimationFrame',
]);

// Libraries that should not be imported in workers
export const UNSAFE_IMPORTS = new Set([
  'react',
  'react-dom',
  '@apollo/client',
  'react-router',
  'react-router-dom',
]);

export interface UnsafeApiUsage {
  file: string;
  line: number;
  column: number;
  api: string;
  workerFile: string;
  message: string;
  dependencyPath: string[];
  type: 'api' | 'import';
}
