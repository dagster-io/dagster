import * as React from 'react';

import {TokenizingFieldValue} from 'src/TokenizingField';
import {RunTag} from 'src/runs/RunTag';
import {RunFragment_tags} from 'src/runs/types/RunFragment';
import {RunTableRunFragment_tags} from 'src/runs/types/RunTableRunFragment';
import {Box} from 'src/ui/Box';

export const RunTags: React.FC<{
  tags: RunTableRunFragment_tags[] | RunFragment_tags[];
  onSetFilter?: (search: TokenizingFieldValue[]) => void;
}> = React.memo(({tags, onSetFilter}) => {
  if (!tags.length) {
    return null;
  }
  const onClick = (tag: RunTableRunFragment_tags) => {
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
