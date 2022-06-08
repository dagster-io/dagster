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

export const RunTags: React.FC<{
  tags: TagType[];
  mode: string | null;
  onSetFilter?: (search: RunFilterToken[]) => void;
}> = React.memo(({tags, onSetFilter, mode}) => {
  const copy = useCopyToClipboard();

  const actions = React.useMemo(() => {
    const list = [
      {
        label: 'Copy tag',
        onClick: (tag: TagType) => {
          copy(`${tag.key}:${tag.value}`);
          SharedToaster.show({intent: 'success', message: 'Copied tag!'});
        },
      },
    ];

    if (onSetFilter) {
      list.push({
        label: 'Add tag to filter',
        onClick: (tag: TagType) => {
          onSetFilter([{token: 'tag', value: `${tag.key}=${tag.value}`}]);
        },
      });
    }

    return list;
  }, [copy, onSetFilter]);

  const displayedTags = React.useMemo(() => {
    const priority = [];
    const others = [];
    for (const tag of tags) {
      if (
        tag.value.startsWith(__ASSET_JOB_PREFIX) &&
        (tag.key === DagsterTag.PartitionSet || tag.key === DagsterTag.StepSelection)
      ) {
        continue;
      } else if (priorityTagSet.has(tag.key)) {
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
        <RunTag tag={tag} key={idx} actions={actions} />
      ))}
    </Box>
  );
});
