import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);

/**
 * Use localStorage to persist the expanded/collapsed visual state of repository containers,
 * e.g. for the left nav or run timeline.
 */
export const useRepoExpansionState = (storageKey: string) => {
  const {basePath} = React.useContext(AppContext);
  const [expandedKeys, setExpandedKeys] = useStateWithStorage<string[]>(
    `${basePath}:dagit.${storageKey}`,
    validateExpandedKeys,
  );

  const onToggle = React.useCallback(
    (repoAddress: RepoAddress) => {
      const key = repoAddressAsString(repoAddress);
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

  return React.useMemo(
    () => ({
      expandedKeys,
      onToggle,
    }),
    [expandedKeys, onToggle],
  );
};
