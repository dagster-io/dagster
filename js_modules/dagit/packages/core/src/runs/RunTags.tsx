import {Box} from '@dagster-io/ui';
import * as React from 'react';

import {SharedToaster} from '../app/DomUtils';
import {useCopyToClipboard} from '../app/browser';

import {RunTag, TagType} from './RunTag';
import {RunFilterToken} from './RunsFilterInput';

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

  if (!tags.length) {
    return null;
  }

  return (
    <Box flex={{direction: 'row', wrap: 'wrap', gap: 4}}>
      {mode ? <RunTag tag={{key: 'mode', value: mode}} /> : null}
      {tags.map((tag, idx) => (
        <RunTag tag={tag} key={idx} actions={actions} />
      ))}
    </Box>
  );
});
