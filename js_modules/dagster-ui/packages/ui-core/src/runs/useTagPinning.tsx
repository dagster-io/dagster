import {useCallback} from 'react';

import {DagsterTag} from './RunTag';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export function useTagPinning() {
  // Most system tags are unpinned by default so we track pinned for these.
  const [pinnedSystemTags, setPinnedSystemTags] = useStateWithStorage(
    'pinned-system-tags',
    validateIsArray,
  );

  // All user tags are pinned by default so we track unpinned.
  const [unpinnedTags, setUnpinnedTags] = useStateWithStorage('unpinned-tags', validateIsArray);

  const onToggleTagPin = useCallback(
    (tagKey: string) => {
      if (isUnpinnedByDefaultSystemTag(tagKey)) {
        setPinnedSystemTags((pinnedSystemTags) => toggleTag(pinnedSystemTags, tagKey));
      } else {
        setUnpinnedTags((unpinnedTags) => toggleTag(unpinnedTags, tagKey));
      }
    },
    [setUnpinnedTags, setPinnedSystemTags],
  );

  const isTagPinned = useCallback(
    (tag: {key: string}) => {
      return isUnpinnedByDefaultSystemTag(tag.key)
        ? pinnedSystemTags.indexOf(tag.key) !== -1
        : unpinnedTags.indexOf(tag.key) === -1;
    },
    [pinnedSystemTags, unpinnedTags],
  );

  return {
    isTagPinned,
    onToggleTagPin,
  };
}

function validateIsArray(value: any) {
  if (Array.isArray(value)) {
    return value;
  }
  return [];
}

function isUnpinnedByDefaultSystemTag(key: string) {
  return (
    (key.startsWith(DagsterTag.Namespace) &&
      key !== DagsterTag.Partition &&
      key !== DagsterTag.Backfill) ||
    key === 'mode'
  );
}

function toggleTag(tagsArr: string[] | undefined, tagKey: string): string[] {
  const tags = tagsArr || [];
  if (tags.indexOf(tagKey) !== -1) {
    return tags.filter((key) => key !== tagKey);
  } else {
    return [...tags, tagKey];
  }
}
