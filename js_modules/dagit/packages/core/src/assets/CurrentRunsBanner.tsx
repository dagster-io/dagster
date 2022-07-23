import {BaseTag, Box, Colors, Spinner} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {LiveDataForNode} from '../asset-graph/Utils';

export const CurrentRunsBanner: React.FC<{liveData?: LiveDataForNode}> = ({liveData}) => {
  const {inProgressRunIds = [], unstartedRunIds = []} = liveData || {};

  if (inProgressRunIds.length === 0 && unstartedRunIds.length === 0) {
    return null;
  }
  return (
    <Box
      background={Colors.Blue50}
      flex={{direction: 'column', gap: 4}}
      border={{side: 'bottom', width: 1, color: Colors.Blue100}}
      padding={{vertical: 12, left: 24, right: 12}}
      style={{color: Colors.Blue700, fontSize: 12, fontWeight: 700}}
    >
      {inProgressRunIds.length > 0 && (
        <Box flex={{gap: 4, alignItems: 'center', wrap: 'wrap'}}>
          {inProgressRunIds.map((runId) => (
            <RunIDTag key={runId} runId={runId} />
          ))}
          <span>
            {' '}
            {inProgressRunIds.length === 1 ? 'is' : 'are'} currently refreshing this asset.
          </span>
        </Box>
      )}
      {unstartedRunIds.length > 0 && (
        <Box flex={{gap: 4, alignItems: 'center', wrap: 'wrap'}}>
          {unstartedRunIds.map((runId) => (
            <RunIDTag key={runId} runId={runId} />
          ))}
          <span>
            {' '}
            {unstartedRunIds.length === 1 ? 'has' : 'have'} started and will refresh this asset.
          </span>
        </Box>
      )}
    </Box>
  );
};

const RunIDTag: React.FC<{runId: string}> = ({runId}) => (
  <BaseTag
    key={runId}
    textColor={Colors.Blue700}
    fillColor={Colors.Blue50}
    label={
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Spinner purpose="caption-text" />
        <Link to={`/instance/runs/${runId}`}>{`Run: ${runId.slice(0, 8)}`}</Link>
      </Box>
    }
  />
);
