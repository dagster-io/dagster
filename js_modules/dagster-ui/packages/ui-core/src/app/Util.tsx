import {cache} from 'idb-lru-cache';
import memoize from 'lodash/memoize';
import LRU from 'lru-cache';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {featureEnabled} from './Flags';
import {timeByParts} from './timeByParts';

function twoDigit(v: number) {
  return `${v < 10 ? '0' : ''}${v}`;
}

function indexesOf(string: string, search: RegExp | string) {
  const indexes: number[] = [];
  const regexp = new RegExp(search, 'g');
  let match = null;
  while ((match = regexp.exec(string))) {
    indexes.push(match.index);
  }
  return indexes;
}

export const withMiddleTruncation = (text: string, options: {maxLength: number}) => {
  const overflowLength = text.length - options.maxLength;
  if (overflowLength <= 0) {
    // No truncation is necessary
    return text;
  }
  if (options.maxLength <= 10) {
    // Middle truncation to this few characters (eg: abc…ef) is kind of silly
    // and just using abcde… looks better.
    return text.substring(0, options.maxLength - 1) + '…';
  }

  // Find all the breakpoints in the string
  //   "my_great_long_solid_name"
  //     ˄     ˄    ˄     ˄
  const breakpoints = text.includes('__') ? indexesOf(text, /__/g) : indexesOf(text, /[_>\.-]/g);

  // Given no breakpoints, slice out the middle of the string. Adding
  // the overflowLength here gives us the END point of the truncated region.
  //
  //   "abc(defg)hijk"
  //            ˄
  let breakpoint = Math.floor((text.length + overflowLength) / 2);

  // Find the first breakpoint that exists AFTER enough characters that we could show
  // at least three prefix letters after cutting out overflowLength.
  const firstUsableIdx = breakpoints.findIndex((bp) => bp > overflowLength + 3);

  if (firstUsableIdx !== -1) {
    // If we found a usable breakpoint, see if we could instead choose the middle
    // breakpoint which would give us more prefix. All else equal,
    // "my_great_l…_name" looks better than "my_g…_solid_name"
    const middleIdx = Math.floor(breakpoints.length / 2);
    const breakpointAtIndex = breakpoints[Math.max(firstUsableIdx, middleIdx)];
    if (breakpointAtIndex !== undefined) {
      breakpoint = breakpointAtIndex;
    }
  }

  const result = [
    text.substring(0, breakpoint - (overflowLength + 1)),
    text.substring(breakpoint),
  ].join('…');

  return result;
};

const msecFormatter = memoize((locale: string) => {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
});

/**
 * Return an i18n-formatted millisecond in seconds as a decimal, with no leading zero.
 */
const formatMsecMantissa = (msec: number) =>
  msecFormatter(navigator.language)
    .format(msec / 1000)
    .slice(-4);

/**
 * Format the time without milliseconds, rounding to :01 for non-zero value within (-1, 1)
 */
export const formatElapsedTimeWithoutMsec = (msec: number) => {
  const {hours, minutes, seconds} = timeByParts(msec);
  const negative = msec < 0;
  const roundedSeconds = msec !== 0 && msec < 1000 && msec > -1000 ? 1 : seconds;
  return `${negative ? '-' : ''}${hours}:${twoDigit(minutes)}:${twoDigit(roundedSeconds)}`;
};

export const formatElapsedTimeWithMsec = (msec: number) => {
  const {hours, minutes, seconds, milliseconds} = timeByParts(msec);

  const negative = msec < 0;
  const sign = negative ? '-' : '';
  const hourStr = hours > 0 ? `${hours}:` : '';
  const minuteStr = hours > 0 ? `${twoDigit(minutes)}:` : minutes > 0 ? `${minutes}:` : '';
  const secStr = hours > 0 || minutes > 0 ? `${twoDigit(seconds)}` : `${seconds}`;
  const mantissa = formatMsecMantissa(milliseconds);

  return `${sign}${hourStr}${minuteStr}${secStr}${mantissa}`;
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

export function asyncMemoize<T, R, U extends (arg: T, ...rest: any[]) => PromiseLike<R>>(
  fn: U,
  hashFn?: (arg: T, ...rest: any[]) => any,
  hashSize?: number,
): U {
  const cache = new LRU(hashSize || 50);
  return (async (arg: T, ...rest: any[]) => {
    const key = hashFn ? hashFn(arg, ...rest) : arg;
    if (cache.has(key)) {
      return Promise.resolve(cache.get(key) as R);
    }
    const r = (await fn(arg, ...rest)) as R;
    cache.set(key, r);
    return r;
  }) as any;
}

export function indexedDBAsyncMemoize<T, R, U extends (arg: T, ...rest: any[]) => Promise<R>>(
  fn: U,
  hashFn?: (arg: T, ...rest: any[]) => any,
): U & {
  isCached: (arg: T, ...rest: any[]) => Promise<boolean>;
} {
  let lru: ReturnType<typeof cache<string, R>> | undefined;
  try {
    lru = cache<string, R>({
      dbName: 'indexDBAsyncMemoizeDB',
      maxCount: 50,
    });
  } catch (e) {}

  async function genHashKey(arg: T, ...rest: any[]) {
    const hash = hashFn ? hashFn(arg, ...rest) : arg;

    const encoder = new TextEncoder();
    // Crypto.subtle isn't defined in insecure contexts... fallback to using the full string as a key
    // https://stackoverflow.com/questions/46468104/how-to-use-subtlecrypto-in-chrome-window-crypto-subtle-is-undefined
    if (crypto.subtle?.digest) {
      const data = encoder.encode(hash.toString());
      const hashBuffer = await crypto.subtle.digest('SHA-1', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
      return hashArray.map((b) => b.toString(16).padStart(2, '0')).join(''); // convert bytes to hex string
    }
    return hash.toString();
  }

  const ret = (async (arg: T, ...rest: any[]) => {
    return new Promise<R>(async (resolve) => {
      const hashKey = await genHashKey(arg, ...rest);
      if (lru && (await lru.has(hashKey))) {
        const {value} = await lru.get(hashKey);
        resolve(value);
        return;
      }

      const result = await fn(arg, ...rest);
      // Resolve the promise before storing the result in IndexedDB
      resolve(result);
      if (lru) {
        await lru.set(hashKey, result, {
          // Some day in the year 2050...
          expiry: new Date(9 ** 13),
        });
      }
    });
  }) as any;
  ret.isCached = async (arg: T, ...rest: any) => {
    const hashKey = await genHashKey(arg, ...rest);
    if (!lru) {
      return false;
    }
    return await lru.has(hashKey);
  };
  return ret;
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

export function assertUnreachable(value: never): never {
  throw new Error(`Didn't expect to get here with value: ${JSON.stringify(value)}`);
}

export function debugLog(...args: any[]) {
  if (featureEnabled(FeatureFlag.flagDebugConsoleLogging)) {
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

// Useful for generating predicates to retain type information when
// find/filtering GraphQL results. Example:
//
// const textMetadata = metadataEntries.filter(gqlTypePredicate('TextMetadataEntry'));
//
// `textMetadata` will be of type `TextMetadataEntry[]`.
export const gqlTypePredicate =
  <T extends string>(typename: T) =>
  <N extends {__typename: string}>(node: N): node is Extract<N, {__typename: T}> => {
    return node.__typename === typename;
  };

export const COMMON_COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base'});
