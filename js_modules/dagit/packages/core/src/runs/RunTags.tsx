import {Box} from '@dagster-io/ui';
import * as React from 'react';

import {SharedToaster} from '../app/DomUtils';
import {useCopyToClipboard} from '../app/browser';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';

import {DagsterTag, RunTag, TagType} from './RunTag';
import {RunFilterToken} from './RunsFilterInput';

// Sort these tags to the start of the list.
export const priorityTagSet = new Set([
  DagsterTag.ScheduleName as string,
  DagsterTag.SensorName as string,
  DagsterTag.Backfill as string,
]);

const renamedTags = {
  [DagsterTag.SolidSelection]: DagsterTag.OpSelection,
};

export const canAddTagToFilter = (key: string) => {
  return key !== DagsterTag.SolidSelection && key !== DagsterTag.OpSelection;
};

export const RunTags: React.FC<{
  tags: TagType[];
  mode: string | null;
  onAddTag?: (token: RunFilterToken) => void;
}> = React.memo(({tags, onAddTag, mode}) => {
  const copy = useCopyToClipboard();

  const copyAction = React.useMemo(
    () => ({
      label: 'Copy tag',
      onClick: (tag: TagType) => {
        copy(`${tag.key}:${tag.value}`);
        SharedToaster.show({intent: 'success', message: 'Copied tag!'});
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
              onAddTag({token: 'tag', value: `${tag.key}=${tag.value}`});
            },
          }
        : null,
    [onAddTag],
  );

  const actionsForTag = (tag: TagType) => {
    const list = [copyAction];
    if (addToFilterAction && canAddTagToFilter(tag.key)) {
      list.push(addToFilterAction);
    }
    return list.filter((item) => !!item);
  };

  const displayedTags = React.useMemo(() => {
    const priority = [];
    const others = [];
    const copiedTags = tags.map(({key, value}) => ({key, value}));
    for (const tag of copiedTags) {
      const {key} = tag;
      if (renamedTags.hasOwnProperty(key)) {
        tag.key = renamedTags[key];
      }

      if (
        tag.value.startsWith(__ASSET_JOB_PREFIX) &&
        (key === DagsterTag.PartitionSet || key === DagsterTag.StepSelection)
      ) {
        continue;
      } else if (priorityTagSet.has(key)) {
        priority.push(tag);
      } else {
        others.push(tag);
      }
    }
    return [...priority, ...others];
  }, [tags]);

  if (!tags.length) {
    return null;
  }

  return (
    <Box flex={{direction: 'row', wrap: 'wrap', gap: 4}}>
      {mode ? <RunTag tag={{key: 'mode', value: mode}} /> : null}
      {displayedTags.map((tag, idx) => (
        <RunTag tag={tag} key={idx} actions={actionsForTag(tag)} />
      ))}
    </Box>
  );
});
