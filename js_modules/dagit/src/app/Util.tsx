import LRU from 'lru-cache';

import {getJSONForKey} from 'src/app/LocalStorage';

export const DEFAULT_RESULT_NAME = 'result';

export function debounce<T extends (...args: any[]) => any>(func: T, wait = 100): T {
  let timeout: any | null = null;
  let args: any[] | null = null;
  let timestamp = 0;
  let result: ReturnType<T>;

  function later() {
    const last = Date.now() - timestamp;

    if (last < wait && last >= 0) {
      timeout = setTimeout(later, wait - last);
    } else {
      timeout = null;
      // eslint-disable-next-line
      result = func.apply(null, args);
      args = null;
    }
  }

  const debounced = function (...newArgs: any[]) {
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
  return `${v < 10 ? '0' : ''}${v}`;
}

export const formatElapsedTime = (msec: number) => {
  if (msec < 10000) {
    return `${(msec / 1000).toFixed(3)}s`;
  }

  const sec = Math.round(msec / 1000) % 60;
  const min = Math.floor(msec / 1000 / 60) % 60;
  const hours = Math.floor(msec / 1000 / 60 / 60);
  return `${hours}:${twoDigit(min)}:${twoDigit(sec)}`;
};

export function breakOnUnderscores(str: string) {
  return str.replace(/_/g, '_\u200b');
}

export function patchCopyToRemoveZeroWidthUnderscores() {
  document.addEventListener('copy', (event) => {
    if (!event.clipboardData) {
      // afaik this is always defined, but the TS field is optional
      return;
    }

    // Note: This returns the text of the current selection if DOM
    // nodes are selected. If the selection on the page is text within
    // codemirror or an input or textarea, this returns "" and we fall
    // through to the default pasteboard content.
    const text = (window.getSelection() || '').toString().replace(/_\u200b/g, '_');

    if (text.length) {
      event.preventDefault();
      event.clipboardData.setData('Text', text);
    }
  });
}

export function memoize<T, R>(
  fn: (arg: T, ...rest: any[]) => R,
  hashFn?: (arg: T, ...rest: any[]) => any,
  hashSize?: number,
): (arg: T, ...rest: any[]) => R {
  const cache = new LRU(hashSize || 50);
  return (arg: T, ...rest: any[]) => {
    const key = hashFn ? hashFn(arg, ...rest) : arg;
    if (cache.has(key)) {
      return cache.get(key) as R;
    }
    const r = fn(arg, ...rest);
    cache.set(key, r);
    return r;
  };
}

export function asyncMemoize<T, R>(
  fn: (arg: T, ...rest: any[]) => PromiseLike<R>,
  hashFn?: (arg: T, ...rest: any[]) => any,
  hashSize?: number,
): (arg: T, ...rest: any[]) => Promise<R> {
  const cache = new LRU(hashSize || 50);
  return async (arg: T, ...rest: any[]) => {
    const key = hashFn ? hashFn(arg, ...rest) : arg;
    if (cache.has(key)) {
      return Promise.resolve(cache.get(key) as R);
    }
    const r = (await fn(arg, ...rest)) as R;
    cache.set(key, r);
    return r;
  };
}

// Simple memoization function for methods that take a single object argument.
// Returns a memoized copy of the provided function which retrieves the result
// from a cache after the first invocation with a given object.
//
// Uses WeakMap to tie the lifecycle of the cache to the lifecycle of the
// object argument.
//
// eslint-disable-next-line @typescript-eslint/ban-types
export function weakmapMemoize<T extends object, R>(
  fn: (arg: T, ...rest: any[]) => R,
): (arg: T, ...rest: any[]) => R {
  const cache = new WeakMap();
  return (arg: T, ...rest: any[]) => {
    if (cache.has(arg)) {
      return cache.get(arg);
    }
    const r = fn(arg, ...rest);
    cache.set(arg, r);
    return r;
  };
}

export function titleOfIO(i: {solid: {name: string}; definition: {name: string}}) {
  return i.solid.name !== DEFAULT_RESULT_NAME
    ? `${i.solid.name}:${i.definition.name}`
    : i.solid.name;
}

export function assertUnreachable(_: never): never {
  throw new Error("Didn't expect to get here");
}

const DAGIT_FLAGS_KEY = 'DAGIT_FLAGS';

export enum FeatureFlag {
  DebugConsoleLogging = 'DebugConsoleLogging',
  LeftNav = 'LeftNav',
}

export function getFeatureFlags(): FeatureFlag[] {
  return getJSONForKey(DAGIT_FLAGS_KEY) || [];
}

export const featureEnabled = (flag: FeatureFlag) => getFeatureFlags().includes(flag);

export function setFeatureFlags(flags: FeatureFlag[]) {
  if (!(flags instanceof Array)) {
    throw new Error('flags must be an array');
  }
  localStorage.setItem(DAGIT_FLAGS_KEY, JSON.stringify(flags));
}

export function debugLog(...args: any[]) {
  if (featureEnabled(FeatureFlag.DebugConsoleLogging)) {
    console.log(...args);
  }
}

export function colorHash(str: string) {
  let seed = 0;
  for (let i = 0; i < str.length; i++) {
    seed = ((seed << 5) - seed + str.charCodeAt(i)) | 0;
  }

  const random255 = (x: number) => {
    const value = Math.sin(x) * 10000;
    return 255 * (value - Math.floor(value));
  };

  return `rgb(${random255(seed++)}, ${random255(seed++)}, ${random255(seed++)})`;
}
