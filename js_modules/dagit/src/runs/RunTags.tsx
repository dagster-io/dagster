import * as React from 'react';

import {RunTag} from 'src/runs/RunTag';
import {Box} from 'src/ui/Box';
import {TokenizingFieldValue} from 'src/ui/TokenizingField';

interface RunTagType {
  key: string;
  value: string;
}

export const RunTags: React.FC<{
  tags: RunTagType[];
  onSetFilter?: (search: TokenizingFieldValue[]) => void;
}> = React.memo(({tags, onSetFilter}) => {
  if (!tags.length) {
    return null;
  }
  const onClick = (tag: RunTagType) => {
    onSetFilter && onSetFilter([{token: 'tag', value: `${tag.key}=${tag.value}`}]);
  };

  return (
    <Box flex={{direction: 'row', wrap: 'wrap'}}>
      {tags.map((tag, idx) => (
        <RunTag tag={tag} key={idx} onClick={onClick} />
      ))}
    </Box>
  );
});
