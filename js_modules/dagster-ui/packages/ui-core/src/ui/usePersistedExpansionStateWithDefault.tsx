import {useCallback, useContext, useMemo} from 'react';

import {AppContext} from '../app/AppContext';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

const validateExpandedKeys = (parsed: unknown): {[key: string]: boolean} =>
  !!parsed && typeof parsed === 'object' && !Array.isArray(parsed)
    ? (parsed as {[key: string]: boolean})
    : {};

/**
 * Use localStorage to persist the expanded/collapsed visual state of rows.
 */
export const usePersistedExpansionStateWithDefault = (
  storageKey: string,
  defaultValue: boolean,
) => {
  const {basePath} = useContext(AppContext);
  const [expandedKeys, setExpandedKeys] = useStateWithStorage<{[key: string]: boolean}>(
    `${basePath}:dagster.${storageKey}`,
    validateExpandedKeys,
  );

  const onToggle = useCallback(
    (key: string) => {
      setExpandedKeys((current) => {
        const nextExpandedKeys = current
          ? {...current, [key]: key in current ? !current[key] : !defaultValue}
          : {[key]: !defaultValue};
        return nextExpandedKeys;
      });
    },
    [setExpandedKeys, defaultValue],
  );

  const isExpanded = useCallback(
    (key: string) => {
      return key in expandedKeys ? expandedKeys[key]! : defaultValue;
    },
    [expandedKeys, defaultValue],
  );

  return useMemo(
    () => ({
      isExpanded,
      onToggle,
    }),
    [isExpanded, onToggle],
  );
};
