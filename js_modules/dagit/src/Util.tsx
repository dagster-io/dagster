export const DEFAULT_RESULT_NAME = "result";

// The address to the dagit server (eg: http://localhost:5000) based
// on our current "GRAPHQL_URI" env var. Note there is no trailing slash.
export const ROOT_SERVER_URI = (process.env.REACT_APP_GRAPHQL_URI || "")
  .replace("wss://", "https://")
  .replace("ws://", "http://")
  .replace("/graphql", "");

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
