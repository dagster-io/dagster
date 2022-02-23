import {Box, ColorsWIP, IconWIP, TagWIP} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

export const RunStepKeysAssetList: React.FC<{
  stepKeys: string[] | null;
  clickableTags?: boolean;
}> = React.memo(({stepKeys, clickableTags}) => {
  if (!stepKeys || !stepKeys.length) {
    return null;
  }

  const displayed = stepKeys.slice(0, 6);
  const hidden = stepKeys.length - displayed.length;

  if (clickableTags) {
    return (
      <Box flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}>
        {displayed.map((stepKey) => (
          <Link to={`/instance/assets/${stepKey}`} key={stepKey}>
            <TagWIP intent="none" interactive icon="asset">
              {stepKey}
            </TagWIP>
          </Link>
        ))}
        {hidden > 0 && (
          <TagWIP intent="none" icon="asset">
            {` + ${hidden} more`}
          </TagWIP>
        )}
      </Box>
    );
  }

  return (
    <Box flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}>
      <IconWIP color={ColorsWIP.Gray400} name="asset" size={16} />
      {`${displayed.join(', ')}${hidden > 0 ? ` + ${hidden} more` : ''}`}
    </Box>
  );
});
