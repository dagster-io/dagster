export const DEFAULT_RESULT_NAME = "result";

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 100
): T {
  let timeout: any | null = null;
  let args: any[] | null = null;
  let timestamp: number = 0;
  let result: ReturnType<T>;

  function later() {
    const last = Date.now() - timestamp;

    if (last < wait && last >= 0) {
      timeout = setTimeout(later, wait - last);
    } else {
      timeout = null;
      result = func.apply(null, args);
      args = null;
    }
  }

  const debounced = function(...newArgs: any[]) {
    timestamp = Date.now();
    args = newArgs;
    if (!timeout) {
      timeout = setTimeout(later, wait);
    }

    return result;
  };

  return (debounced as any) as T;
}
