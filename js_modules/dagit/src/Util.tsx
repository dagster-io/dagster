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

function twoDigit(v: number) {
  return `${v < 10 ? "0" : ""}${v}`;
}

export function formatElapsedTime(elapsed: number) {
  let text = "";

  if (elapsed < 1000) {
    // < 1 second, show "X msec"
    text = `${Math.ceil(elapsed)} msec`;
  } else {
    // < 1 hour, show "42:12"
    const sec = Math.floor(elapsed / 1000) % 60;
    const min = Math.floor(elapsed / 1000 / 60) % 60;
    const hours = Math.floor(elapsed / 1000 / 60 / 60);

    if (hours > 0) {
      text = `${hours}:${twoDigit(min)}:${twoDigit(sec)}`;
    } else {
      text = `${min}:${twoDigit(sec)}`;
    }
  }
  return text;
}

// Simple memoization function for methods that take a single object argument.
// Returns a memoized copy of the provided function which retrieves the result
// from a cache after the first invocation with a given object.
//
// Uses WeakMap to tie the lifecycle of the cache to the lifecycle of the
// object argument.
//
export function weakmapMemoize<T extends object, R>(
  fn: (arg: T) => R
): (arg: T) => R {
  let cache = new WeakMap();
  return (arg: T) => {
    if (cache.has(arg)) {
      return cache.get(arg);
    }
    const r = fn(arg);
    cache.set(arg, r);
    return r;
  };
}
