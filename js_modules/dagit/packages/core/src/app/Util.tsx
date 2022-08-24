import LRU from 'lru-cache';

import {featureEnabled, FeatureFlag} from './Flags';
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
  if (options.maxLength <= 6) {
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
    breakpoint = breakpoints[Math.max(firstUsableIdx, middleIdx)];
  }

  const result = [
    text.substring(0, breakpoint - (overflowLength + 1)),
    text.substring(breakpoint),
  ].join('…');

  return result;
};

/**
 * Return an i18n-formatted millisecond in seconds as a decimal, with no leading zero.
 */
const formatMsecMantissa = (msec: number) =>
  (msec / 1000)
    .toLocaleString(navigator.language, {
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    })
    .slice(-4);

/**
 * Opinionated elapsed time formatting:
 *
 * - Times between -10 and 10 seconds are shown as `X.XXXs`
 * - Otherwise times are rendered in a `X:XX:XX` format, without milliseconds
 */
export const formatElapsedTime = (msec: number) => {
  const {hours, minutes, seconds, milliseconds} = timeByParts(msec);
  const negative = msec < 0;

  if (msec < 10000 && msec > -10000) {
    const formattedMsec = formatMsecMantissa(milliseconds);
    return `${negative ? '-' : ''}${seconds}${formattedMsec}s`;
  }

  return `${negative ? '-' : ''}${hours}:${twoDigit(minutes)}:${twoDigit(seconds)}`;
};

export const formatElapsedTimeWithMsec = (msec: number) => {
  const {hours, minutes, seconds, milliseconds} = timeByParts(msec);
  const negative = msec < 0;
  const positiveValue = `${hours}:${twoDigit(minutes)}:${twoDigit(seconds)}${formatMsecMantissa(
    milliseconds,
  )}`;
  return `${negative ? '-' : ''}${positiveValue}`;
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

export function assertUnreachable(_: never): never {
  throw new Error("Didn't expect to get here");
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
export const gqlTypePredicate = <T extends string>(typename: T) => <N extends {__typename: string}>(
  node: N,
): node is Extract<N, {__typename: T}> => {
  return node.__typename === typename;
};
