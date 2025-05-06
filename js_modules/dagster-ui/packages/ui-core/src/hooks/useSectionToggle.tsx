import {useMemo} from 'react';

import {useStateWithStorage} from './useStateWithStorage';
import {usePrefixedCacheKey} from '../app/usePrefixedCacheKey';

/**
 * Hook to manage open/closed state for sectioned lists or grids.
 * Returns a Set of closed section ids and a toggle function for a given id.
 */
export function useSectionToggle(storageKey: string) {
  const key = usePrefixedCacheKey(storageKey);
  const [closedSections, setClosedSections] = useStateWithStorage<string[]>(key, (value) =>
    value instanceof Array ? value : [],
  );
  const closedSectionsSet = useMemo(() => new Set(closedSections), [closedSections]);

  const toggleSection = (id: string) => {
    setClosedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return Array.from(newSet);
    });
  };

  return {closedSectionsSet, toggleSection};
}
