import {useCallback} from 'react';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {DagsterTag} from '../RunTag';

// The row decides when and how to show these, so they can't be pinned by the user.
const AUTOMATICALLY_SHOWN_TAG_KEYS = new Set<string>([
  DagsterTag.Partition,
  DagsterTag.AssetPartitionRangeStart,
  DagsterTag.AssetPartitionRangeEnd,
  DagsterTag.Backfill,
  DagsterTag.ScheduleName,
  DagsterTag.SensorName,
  DagsterTag.ParentRunId,
  DagsterTag.User,
]);

export const canPinTag = (key: string) => !AUTOMATICALLY_SHOWN_TAG_KEYS.has(key);

const validatePinnedTagKeys = (json: unknown): string[] => {
  if (!Array.isArray(json)) {
    return [];
  }
  return json.filter((key): key is string => typeof key === 'string');
};

export const usePinnedRunTags = () => {
  const [pinnedTagKeys, setPinnedTagKeys] = useStateWithStorage(
    'pinned-run-tags',
    validatePinnedTagKeys,
  );

  const isTagPinned = useCallback((key: string) => pinnedTagKeys.includes(key), [pinnedTagKeys]);

  const togglePin = useCallback(
    (key: string) =>
      setPinnedTagKeys((current) =>
        current.includes(key) ? current.filter((pinned) => pinned !== key) : [...current, key],
      ),
    [setPinnedTagKeys],
  );

  return {pinnedTagKeys, isTagPinned, togglePin};
};
