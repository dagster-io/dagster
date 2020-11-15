import querystring from 'query-string';
import React from 'react';
import {useHistory, useLocation} from 'react-router-dom';

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
export function useQueryPersistedState<
  T extends {[key: string]: any} | Array<any> | (string | undefined)
>(options: {
  queryKey?: string;
  defaults?: {[key: string]: any};
  decode?: (raw: {[key: string]: any}) => T;
  encode?: (raw: T) => {[key: string]: any};
}): [T, (updates: T) => void] {
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
  const qs = React.useRef<{[key: string]: any}>({});
  qs.current = querystring.parse(location.search);

  const qsWithDefaults = {...(defaults || {}), ...qs.current};
  const qsDecoded = decode ? decode(qsWithDefaults) : (qsWithDefaults as T);

  return [
    qsDecoded,
    (updated: T) => {
      history.replace(
        `${location.pathname}?${querystring.stringify({
          ...qs.current,
          ...(encode ? encode(updated) : (updated as {[key: string]: any})),
        })}`,
      );
    },
  ];
}
