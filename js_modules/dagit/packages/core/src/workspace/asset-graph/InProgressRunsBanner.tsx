import React from 'react';
import {Link} from 'react-router-dom';

import {BaseTag} from '../../ui/BaseTag';
import {Box} from '../../ui/Box';
import {ColorsWIP} from '../../ui/Colors';
import {Spinner} from '../../ui/Spinner';

export const InProgressRunsBanner: React.FC<{runIds: string[]}> = ({runIds}) => {
  if (runIds.length === 0) {
    return null;
  }
  return (
    <Box
      background={ColorsWIP.Blue50}
      flex={{direction: 'row', gap: 4, alignItems: 'center'}}
      border={{side: 'bottom', width: 1, color: ColorsWIP.Blue100}}
      padding={{vertical: 12, left: 24, right: 12}}
      style={{color: ColorsWIP.Blue700, fontSize: 12, fontWeight: 700}}
    >
      {runIds.map((runId) => (
        <BaseTag
          key={runId}
          textColor={ColorsWIP.Blue700}
          fillColor={ColorsWIP.Blue50}
          label={
            <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
              <Spinner purpose="caption-text" />
              <Link to={`/instance/runs/${runId}`}>{`Run: ${runId.slice(0, 8)}`}</Link>
            </Box>
          }
        />
      ))}
      <span> {runIds.length === 1 ? 'is' : 'are'} currently refreshing this asset.</span>
    </Box>
  );
};
