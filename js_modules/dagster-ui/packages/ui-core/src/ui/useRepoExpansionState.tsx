import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);
export const buildStorageKey = (basePath: string, key: string) => `${basePath}:dagit.${key}`;

/**
 * Use localStorage to persist the expanded/collapsed visual state of repository containers,
 * e.g. for the left nav or run timeline.
 */
export const useRepoExpansionState = (collapsedKey: string, allKeys: string[]) => {
  const {basePath} = React.useContext(AppContext);

  const collapsedStorageKey = buildStorageKey(basePath, collapsedKey);
  const [collapsedKeys, setCollapsedKeys] = useStateWithStorage<string[]>(
    collapsedStorageKey,
    validateExpandedKeys,
  );

  const onToggle = React.useCallback(
    (repoAddress: RepoAddress) => {
      const key = repoAddressAsHumanString(repoAddress);
      setCollapsedKeys((current) => {
        const nextCollapsedKeys = new Set(current || []);
        if (nextCollapsedKeys.has(key)) {
          nextCollapsedKeys.delete(key);
        } else {
          nextCollapsedKeys.add(key);
        }
        return Array.from(nextCollapsedKeys);
      });
    },
    [setCollapsedKeys],
  );

  const onToggleAll = React.useCallback(
    (expand: boolean) => {
      setCollapsedKeys((current) => {
        const nextCollapsedKeys = new Set(current || []);
        allKeys.forEach((key) => {
          expand ? nextCollapsedKeys.delete(key) : nextCollapsedKeys.add(key);
        });
        return Array.from(nextCollapsedKeys);
      });
    },
    [allKeys, setCollapsedKeys],
  );

  const expandedKeys = React.useMemo(() => {
    const collapsedSet = new Set(collapsedKeys);
    return allKeys.filter((key) => !collapsedSet.has(key));
  }, [allKeys, collapsedKeys]);

  return React.useMemo(
    () => ({
      expandedKeys,
      onToggle,
      onToggleAll,
    }),
    [expandedKeys, onToggle, onToggleAll],
  );
};
