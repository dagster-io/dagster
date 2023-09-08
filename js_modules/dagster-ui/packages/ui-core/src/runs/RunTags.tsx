import {Box} from '@dagster-io/ui-components';
import * as React from 'react';

import {showSharedToaster} from '../app/DomUtils';
import {useCopyToClipboard} from '../app/browser';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {TagAction} from '../ui/TagActions';

import {DagsterTag, RunTag, TagType} from './RunTag';
import {RunFilterToken} from './RunsFilterInput';

// Sort these tags to the start of the list.
const priorityTags = ['mode', DagsterTag.Backfill as string, DagsterTag.Partition as string];
const priorityTagsSet = new Set(priorityTags);

const renamedTags = {
  [DagsterTag.SolidSelection]: DagsterTag.OpSelection,
};

const canAddTagToFilter = (key: string) => {
  return key !== DagsterTag.SolidSelection && key !== DagsterTag.OpSelection && key !== 'mode';
};

export const RunTags: React.FC<{
  tags: TagType[];
  mode?: string | null;
  onAddTag?: (token: RunFilterToken) => void;
  onToggleTagPin?: (key: string) => void;
}> = React.memo(({tags, onAddTag, onToggleTagPin, mode}) => {
  const copy = useCopyToClipboard();

  const copyAction = React.useMemo(
    () => ({
      label: 'Copy tag',
      onClick: async (tag: TagType) => {
        copy(`${tag.key}:${tag.value}`);
        await showSharedToaster({intent: 'success', message: 'Copied tag!'});
      },
    }),
    [copy],
  );

  const addToFilterAction = React.useMemo(
    () =>
      onAddTag
        ? {
            label: 'Add tag to filter',
            onClick: (tag: TagType) => {
              onAddTag({token: 'tag', value: `${tag.originalKey || tag.key}=${tag.value}`});
            },
          }
        : null,
    [onAddTag],
  );

  const actionsForTag = (tag: TagType) => {
    const list: TagAction[] = [copyAction];
    if (addToFilterAction && canAddTagToFilter(tag.key)) {
      list.push(addToFilterAction);
    }
    if (onToggleTagPin) {
      list.push({
        label: tag.pinned ? 'Hide tag' : 'Show tag in table',
        onClick: () => {
          onToggleTagPin(tag.originalKey || tag.key);
        },
      });
    }
    return list.filter((item) => !!item);
  };

  const displayedTags = React.useMemo(() => {
    const priority = [];
    const others = [];
    const copiedTags: TagType[] = tags.map(({key, value, pinned, link}) => ({
      key,
      value,
      pinned,
      link,
    }));
    for (const tag of copiedTags) {
      const {key} = tag;
      if (renamedTags.hasOwnProperty(key)) {
        tag.key = renamedTags[key as keyof typeof renamedTags];
        tag.originalKey = key;
      }

      if (
        tag.value.startsWith(__ASSET_JOB_PREFIX) &&
        (key === DagsterTag.PartitionSet || key === DagsterTag.StepSelection)
      ) {
        continue;
      } else if (priorityTagsSet.has(key)) {
        priority.push(tag);
      } else {
        others.push(tag);
      }
    }
    return [
      ...priority.sort((a, b) => {
        const aIndex = priorityTags.indexOf(a.key);
        const bIndex = priorityTags.indexOf(b.key);
        return aIndex - bIndex;
      }),
      ...others,
    ];
  }, [tags]);

  if (!tags.length) {
    return null;
  }

  const modeTag = mode ? (
    <RunTag tag={{key: 'mode', value: mode}} actions={actionsForTag({key: 'mode', value: mode})} />
  ) : null;
  return (
    <Box flex={{direction: 'row', wrap: 'wrap', gap: 4}}>
      {modeTag}
      {displayedTags.map((tag) => (
        <RunTag tag={tag} key={tag.key} actions={actionsForTag(tag)} />
      ))}
    </Box>
  );
});
