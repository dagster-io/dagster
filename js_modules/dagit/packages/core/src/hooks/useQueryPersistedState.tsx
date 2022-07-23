import isEqual from 'lodash/isEqual';
import qs from 'qs';
import React from 'react';
import {useHistory, useLocation} from 'react-router-dom';

type QueryPersistedDataType =
  | {[key: string]: any}
  | Array<any>
  | (string | undefined | number)
  | (boolean | undefined)
  | null;

let currentQueryString: {[key: string]: any} = {};

export type QueryPersistedStateConfig<T extends QueryPersistedDataType> = {
  queryKey?: string;
  defaults?: {[key: string]: any};
  decode?: (raw: {[key: string]: any}) => T;
  encode?: (raw: T) => {[key: string]: any};
};

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
): [T, (updates: T) => void] {
  const {queryKey, defaults} = options;
  let {encode, decode} = options;

  if (queryKey) {
    // Just a short-hand way of providing encode/decode that go from qs object => string
    if (!encode) {
      encode = (raw: T) => ({[queryKey]: raw});
    }
    if (!decode) {
      decode = (qs: {[key: string]: any}) => inferTypeOfQueryParam<T>(qs[queryKey]);
    }
  }

  const location = useLocation();
  const history = useHistory();

  // We stash the query string into a ref so that the setter can operate on the /current/
  // location even if the user retains it and calls it after other query string changes.
  currentQueryString = qs.parse(location.search, {ignoreQueryPrefix: true});

  const qsWithDefaults = {...(defaults || {}), ...currentQueryString};

  // Note: If you have provided defaults and no encoder/decoder, the `value` exposed by
  // useQueryPersistedState only includes those keys so other params don't leak into your value.
  const qsDecoded = decode ? decode(qsWithDefaults) : inferTypeOfQueryParams<T>(qsWithDefaults);

  // If `decode` yields a non-primitive type (eg: object or array), by default we yield
  // an object with a new identity on every render. To prevent possible render loops caused by
  // our value as a useEffect dependency, etc., we re-use the last yielded object if it isEqual.
  const valueRef = React.useRef<T>(qsDecoded);
  const onChangeRef = React.useCallback<(updated: T) => void>(
    (updated: T) => {
      const next = {
        ...currentQueryString,
        ...(encode ? encode(updated) : (updated as {[key: string]: any})),
      };

      // omit any keys that are equal to the defaults to keep URLs minimal
      for (const [key, value] of Object.entries(next)) {
        if (options.defaults && options.defaults[key] === value) {
          delete next[key];
        }
      }

      currentQueryString = next;
      history.replace(`${location.pathname}?${qs.stringify(next, {arrayFormat: 'brackets'})}`);
    },
    [history, encode, location.pathname, options],
  );

  if (!isEqual(valueRef.current, qsDecoded)) {
    valueRef.current = qsDecoded;
  }
  return [valueRef.current, onChangeRef];
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
