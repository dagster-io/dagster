import {useCallback, useMemo} from 'react';

import {usePrefixedCacheKey} from '../app/usePrefixedCacheKey';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const MAX_RECENT_SUGGESTIONS = 4;

// More are retained than shown, so raising the display count doesn't start from scratch.
const MAX_STORED_SELECTIONS = 10;

const EMPTY: string[] = [];

const noop = () => {};

// Stored data can come from an older build or another tab, so re-apply the write rules.
const validateRecents = (json: any): string[] => {
  if (!Array.isArray(json)) {
    return EMPTY;
  }
  const seen = new Set<string>();
  for (const value of json) {
    if (typeof value === 'string' && value.trim() && !seen.has(value)) {
      seen.add(value.trim());
      if (seen.size === MAX_STORED_SELECTIONS) {
        break;
      }
    }
  }
  return seen.size ? Array.from(seen) : EMPTY;
};

// Inputs sharing a key share their history. Pass `undefined` to disable.
export function useRecentSelections(key: string | undefined) {
  const storageKey = usePrefixedCacheKey(`recent-selections/${key ?? 'disabled'}`);
  const [stored, setStored] = useStateWithStorage<string[]>(storageKey, validateRecents);

  const addRecentInner = useCallback(
    (value: string) => {
      const trimmed = value.trim();
      if (!trimmed) {
        return;
      }
      setStored((prev) =>
        [trimmed, ...(prev ?? []).filter((item) => item !== trimmed)].slice(
          0,
          MAX_STORED_SELECTIONS,
        ),
      );
    },
    [setStored],
  );

  return useMemo(
    () =>
      key
        ? {recentSelections: stored, addRecentSelection: addRecentInner}
        : {recentSelections: EMPTY, addRecentSelection: noop},
    [key, stored, addRecentInner],
  );
}
