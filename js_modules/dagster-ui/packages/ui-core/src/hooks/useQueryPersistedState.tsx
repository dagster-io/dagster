import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';
import qs from 'qs';
import {useCallback, useMemo, useRef} from 'react';
import {useHistory, useLocation} from 'react-router-dom';

import {useSetStateUpdateCallback} from './useSetStateUpdateCallback';
import {COMMON_COLLATOR} from '../app/Util';

export type QueryPersistedDataType =
  | {[key: string]: QueryPersistedDataType}
  | Array<QueryPersistedDataType>
  | Set<QueryPersistedDataType>
  | string
  | undefined
  | number
  | boolean
  | null;

let currentQueryString: qs.ParsedQs = {};

export type QueryPersistedStateConfig<T extends QueryPersistedDataType> = {
  queryKey?: string;
  defaults?: qs.ParsedQs;
  decode?: (raw: qs.ParsedQs) => T;
  encode?: (raw: T) => qs.ParsedQs;
  behavior?: 'push' | 'replace';
};

const defaultEncode = memoize(<T extends QueryPersistedDataType>(queryKey: string) => {
  return (raw: T) => {
    return {[queryKey]: raw} as qs.ParsedQs;
  };
});
const defaultDecode = memoize(
  <T extends QueryPersistedDataType>(queryKey: string) =>
    (qs: {[key: string]: QueryPersistedDataType}) =>
      inferTypeOfQueryParam<T>(qs[queryKey]),
);

const ARRAY_LIMIT = 1000;

/**
 * This goal of this hook is to make it easy to replace `React.useState` with a version
 * that persists the value to the page querystring so it is saved across page reload, etc.
 * Hopefully by making it easy, we'll do this often and improve overall UX.
 *
 * Examples:
 *
 * // Single (string | undefined) key saved to querystring with default value applied inline
 *
 * const [search = '', setSearch] = useQueryPersistedState({queryKey: 'q'})
 *
 * // Object saved to querystring with default values pre-filled
 * // Note: String and boolean values are automatically encoded / decoded, see below for others
 *
 * const [query, setQuery] = useQueryPersistedState<{cursor: string, filter: string}>({
 *   defaults: {cursor: '', filter: ''},
 * })
 *
 * // Custom transformer mapping to / from querystring representation (for our filter tokens)
 * // Note: `setIdeas` will be a different function on every render unless you memoize the options
 * // passed to the hook! Pull the encode/decode functions out into a file constant or use React.useRef
 *
 * const [ideas, setIdeas] = useQueryPersistedState<string[]>({
 *   encode: (ideas) => ({q: ideas.join(',')}),
 *   decode: ({q}) => (q || '').split(','),
 * })
 *
 * Note: if you combine encode/decode with defaults, the defaults are applied to the query
 * string BEFORE decoding.
 */
export function useQueryPersistedState<T extends QueryPersistedDataType>(
  options: QueryPersistedStateConfig<T>,
): [T, React.Dispatch<React.SetStateAction<T>>] {
  const {queryKey, defaults, behavior = 'replace'} = options;
  let {encode, decode} = options;

  if (queryKey) {
    // Just a short-hand way of providing encode/decode that go from qs object => string
    if (!encode) {
      encode = defaultEncode(queryKey);
    }
    if (!decode) {
      decode = defaultDecode(queryKey);
    }
  }

  const location = useLocation();
  const history = useHistory();

  // Note: If you have provided defaults and no encoder/decoder, the `value` exposed by
  // useQueryPersistedState only includes those keys so other params don't leak into your value.
  const qsDecoded = useMemo(() => {
    // We stash the query string into a ref so that the setter can operate on the /current/
    // location even if the user retains it and calls it after other query string changes.
    try {
      currentQueryString = qs.parse(location.search, {
        ignoreQueryPrefix: true,
        // @ts-expect-error QS types are out of date.
        throwOnLimitExceeded: true,
        arrayLimit: ARRAY_LIMIT,
      });
    } catch {
      console.error(
        `Very large array (>${ARRAY_LIMIT} items) detected in query string. This will be permitted, but should be investigated.`,
      );
      // After logging the issue, permit arbitrarily large arrays in order to avoid breaking
      // the app. This might be slow for users, but we won't end up with unexpected objects replacing
      // any arrays. https://github.com/ljharb/qs?tab=readme-ov-file#parsing-arrays
      // This is a pretty unlikely situation: GET request querystrings will be limited by length,
      // and in any case, we shouldn't have many interfaces in the app that allow unbounded arrays to be encoded
      // in querystrings.
      currentQueryString = qs.parse(location.search, {
        ignoreQueryPrefix: true,
        arrayLimit: Infinity,
      });
    }

    const qsWithDefaults = {
      ...(defaults || {}),
      ...currentQueryString,
    };
    return decode ? decode(qsWithDefaults) : inferTypeOfQueryParams<T>(qsWithDefaults);
  }, [location.search, decode, defaults]);

  // If `decode` yields a non-primitive type (eg: object or array), by default we yield
  // an object with a new identity on every render. To prevent possible render loops caused by
  // our value as a useEffect dependency, etc., we re-use the last yielded object if it isEqual.
  const valueRef = useRef<T>(qsDecoded);
  const onChangeRef = useCallback<(updated: T) => void>(
    (updated: T) => {
      const next: qs.ParsedQs = {
        ...currentQueryString,
        ...(encode ? encode(updated) : (updated as qs.ParsedQs)),
      };

      // omit any keys that are equal to the defaults to keep URLs minimal
      for (const [key, value] of Object.entries(next)) {
        if (options.defaults && options.defaults[key] === value) {
          delete next[key];
        }
      }

      // Check if the query has changed. If so, perform a replace. Otherwise, do nothing
      // to ensure that we don't end up in a `replace` loop. If we're not in prod, always run
      // the `replace` so that we surface any unwanted loops during development.
      if (
        (process.env.NODE_ENV !== 'production' && behavior === 'replace') ||
        !areQueriesEqual(currentQueryString, next)
      ) {
        currentQueryString = next;
        const nextPath = `${history.location.pathname}?${qs.stringify(next, {arrayFormat: 'indices'})}`;
        if (behavior === 'replace') {
          history.replace(nextPath);
        } else {
          history.push(nextPath);
        }
      }
    },
    [encode, options.defaults, behavior, history],
  );

  if (!isEqual(valueRef.current, qsDecoded)) {
    valueRef.current = qsDecoded;
  }
  return [valueRef.current, useSetStateUpdateCallback(valueRef.current, onChangeRef)];
}

// Stringify two query objects to check whether they have the same value. Explicitly sort the
// keys, since key order is otherwise undefined.
function areQueriesEqual(queryA: qs.ParsedQs, queryB: qs.ParsedQs) {
  const stringA = qs.stringify(queryA, {
    arrayFormat: 'brackets',
    sort: (a, b) => COMMON_COLLATOR.compare(a, b),
  });
  const stringB = qs.stringify(queryB, {
    arrayFormat: 'brackets',
    sort: (a, b) => COMMON_COLLATOR.compare(a, b),
  });
  return stringA === stringB;
}

function inferTypeOfQueryParam<T>(q: any): T {
  return q === 'false' ? false : q === 'true' ? true : q;
}

function inferTypeOfQueryParams<T>(qs: {[key: string]: any}) {
  const result: {[key: string]: any} = {};
  for (const key of Object.keys(qs)) {
    result[key] = inferTypeOfQueryParam<any>(qs[key]);
  }
  return result as T;
}
