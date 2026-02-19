// Mock for @koale/useworker - the package only provides ESM exports
// (no CJS/require entry), which jest cannot resolve. Since web workers
// don't function in jsdom anyway, this mock passes the function through directly.

export const WORKER_STATUS = {
  PENDING: 'PENDING',
  SUCCESS: 'SUCCESS',
  RUNNING: 'RUNNING',
  ERROR: 'ERROR',
  TIMEOUT_EXPIRED: 'TIMEOUT_EXPIRED',
} as const;

export function useWorker(fn: (...args: any[]) => any) {
  return [fn, {status: WORKER_STATUS.SUCCESS, kill: () => {}}] as const;
}
