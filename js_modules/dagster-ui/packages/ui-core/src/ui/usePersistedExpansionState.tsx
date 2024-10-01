import {useCallback, useContext, useMemo} from 'react';

import {AppContext} from '../app/AppContext';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);
/**
 * Use localStorage to persist the expanded/collapsed visual state of rows.
 */
export const usePersistedExpansionState = (storageKey: string) => {
  const {basePath} = useContext(AppContext);
  const [expandedKeys, setExpandedKeys] = useStateWithStorage<string[]>(
    `${basePath}:dagster.${storageKey}`,
    validateExpandedKeys,
  );

  const onToggle = useCallback(
    (key: string) => {
      setExpandedKeys((current) => {
        const nextExpandedKeys = new Set(current || []);
        if (nextExpandedKeys.has(key)) {
          nextExpandedKeys.delete(key);
        } else {
          nextExpandedKeys.add(key);
        }
        return Array.from(nextExpandedKeys);
      });
    },
    [setExpandedKeys],
  );

  return useMemo(
    () => ({
      expandedKeys,
      onToggle,
    }),
    [expandedKeys, onToggle],
  );
};
