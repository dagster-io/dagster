import isEqual from 'lodash/isEqual';
import querystring from 'query-string';
import React from 'react';
import {useHistory, useLocation} from 'react-router-dom';

type QueryPersistedDataType =
  | {[key: string]: any}
  | Array<any>
  | (string | undefined | number)
  | null;

interface QuerySerializer<T extends QueryPersistedDataType> {
  decode: (raw: {[key: string]: any}) => T;
  encode: (raw: T) => {[key: string]: any};
}

let currentQueryString: {[key: string]: any} = {};

/**
 * This goal of this hook is to make it easy to replace `React.useState` with a version
 * that persists the value to the page querystring so it is saved across page reload, etc.
 * Hopefully by making it easy, we'll do this often and improve overall UX.
 *
 * Examples:
 *
 * // Single (string | undefined) key saved to querystring with default value applied inline
 * const [search = '', setSearch] = useQueryPersistedState({queryKey: 'q'})
 *
 * // Object saved to querystring with default values pre-filled
 * const [query, setQuery] = useQueryPersistedState<{cursor: string, filter: string}>({
 *   defaults: {cursor: '', filter: ''},
 * })
 *
 * // Custom transformer mapping to / from querystring representation (for our filter tokens)
 * const [ideas, setIdeas] = useQueryPersistedState<string[]>({
 *   encode: (ideas) => ({q: ideas.join(',')}),
 *   decode: ({q}) => (q || '').split(','),
 * })
 *
 * Note: if you combine encode/decode with defaults, the defaults are applied to the query
 * string BEFORE decoding.
 */
export function useQueryPersistedState<T extends QueryPersistedDataType>(
  options: {
    queryKey?: string;
    defaults?: {[key: string]: any};
  } & Partial<QuerySerializer<T>>,
): [T, (updates: T) => void] {
  const {queryKey, defaults} = options;
  let {encode, decode} = options;

  if (queryKey) {
    // Just a short-hand way of providing encode/decode that go from qs object => string
    encode = (raw: T) => ({[queryKey]: raw});
    decode = (qs: {[key: string]: any}) => qs[queryKey];
  }

  const location = useLocation();
  const history = useHistory();

  // We stash the query string into a ref so that the setter can operate on the /current/
  // location even if the user retains it and calls it after other query string changes.
  currentQueryString = querystring.parse(location.search);

  const qsWithDefaults = {...(defaults || {}), ...currentQueryString};
  const qsDecoded = decode ? decode(qsWithDefaults) : (qsWithDefaults as T);

  // If `decode` yields a non-primitive type (eg: object or array), by default we yield
  // an object with a new identity on every render. To prevent possible render loops caused by
  // our value as a useEffect dependency, etc., we re-use the last yielded object if it isEqual.
  const valueRef = React.useRef<T>(qsDecoded);
  if (!isEqual(valueRef.current, qsDecoded)) {
    valueRef.current = qsDecoded;
  }

  return [
    valueRef.current,
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
      history.replace(`${location.pathname}?${querystring.stringify(next)}`);
    },
  ];
}
