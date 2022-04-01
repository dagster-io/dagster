import {Warning} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {LiveDataForNode, __ASSET_GROUP} from '../asset-graph/Utils';
import {titleForRun} from '../runs/RunUtils';
import {runsPathWithFilters} from '../runs/RunsFilterInput';

export const FailedRunsSinceMaterializationBanner: React.FC<{liveData?: LiveDataForNode}> = ({
  liveData,
}) => {
  const {runWhichFailedToMaterialize} = liveData || {};

  if (runWhichFailedToMaterialize) {
    return (
      <Warning errorBackground>
        <span>
          Run{' '}
          <Link to={`/instance/runs/${runWhichFailedToMaterialize.id}`}>
            {titleForRun({runId: runWhichFailedToMaterialize.id})}
          </Link>{' '}
          failed to materialize this asset
        </span>
      </Warning>
    );
  }
  return null;
};
