import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);
export const buildStorageKey = (basePath: string, key: string) => `${basePath}:dagit.${key}`;

/**
 * Use localStorage to persist the expanded/collapsed visual state of repository containers,
 * e.g. for the left nav or run timeline.
 */
export const useRepoExpansionState = (
  // todo dish: Delete this arg.
  expandedKey: string,
  collapsedKey: string,
  allKeys: string[],
) => {
  const {basePath} = React.useContext(AppContext);

  // todo dish: Delete this.
  const expandedStorageKey = buildStorageKey(basePath, expandedKey);
  const [expandedKeysDeleteMe] = useStateWithStorage<string[]>(
    expandedStorageKey,
    validateExpandedKeys,
  );

  const collapsedStorageKey = buildStorageKey(basePath, collapsedKey);
  const [collapsedKeys, setCollapsedKeys] = useStateWithStorage<string[]>(
    collapsedStorageKey,
    validateExpandedKeys,
  );

  const needsInversion =
    window.localStorage.getItem(expandedStorageKey) !== null &&
    window.localStorage.getItem(collapsedStorageKey) === null;

  /**
   * Temporary: If the user has been using this feature already, they have been tracking
   * "expanded" state instead of "collapsed" state. Immediately invert the tracked state,
   * using the current "expanded" keys and the full list of keys.
   *
   * todo dish: Delete this effect at some point in November 2022.
   */
  React.useEffect(() => {
    if (needsInversion) {
      setCollapsedKeys(() => allKeys.filter((key) => !expandedKeysDeleteMe.includes(key)));
    }
  });

  const onToggle = React.useCallback(
    (repoAddress: RepoAddress) => {
      const key = repoAddressAsString(repoAddress);
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
