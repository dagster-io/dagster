import * as React from 'react';

import {Box} from '../ui/Box';
import {TokenizingFieldValue} from '../ui/TokenizingField';

import {RunTag} from './RunTag';

interface RunTagType {
  key: string;
  value: string;
}

export const RunTags: React.FC<{
  tags: RunTagType[];
  mode: string | null;
  onSetFilter?: (search: TokenizingFieldValue[]) => void;
}> = React.memo(({tags, onSetFilter, mode}) => {
  if (!tags.length) {
    return null;
  }

  const onClick = (tag: RunTagType) => {
    onSetFilter && onSetFilter([{token: 'tag', value: `${tag.key}=${tag.value}`}]);
  };

  return (
    <Box flex={{direction: 'row', wrap: 'wrap', gap: 4}}>
      {mode ? <RunTag tag={{key: 'mode', value: mode}} /> : null}
      {tags.map((tag, idx) => (
        <RunTag tag={tag} key={idx} onClick={onClick} />
      ))}
    </Box>
  );
});
