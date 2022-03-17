import {Warning} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {titleForRun} from '../../runs/RunUtils';
import {runsPathWithFilters} from '../../runs/RunsFilterInput';

import {LiveDataForNode, __ASSET_GROUP} from './Utils';

export const FailedRunsSinceMaterializationBanner: React.FC<{liveData?: LiveDataForNode}> = ({
  liveData,
}) => {
  const {runsSinceMaterialization, runWhichFailedToMaterialize} = liveData || {};

  if (runsSinceMaterialization) {
    const {jobNames, count} = runsSinceMaterialization;
    const jobNamesCleaned = jobNames.map((j) =>
      j === __ASSET_GROUP ? 'Asset materialization runs' : j,
    );
    const jobNamesSummary =
      jobNamesCleaned.length > 1
        ? `${jobNamesCleaned.slice(0, -1).join(', ')} and ${jobNamesCleaned.slice(-1)[0]}`
        : jobNamesCleaned[0];

    const jobsPage = runsPathWithFilters(
      jobNames.length === 1 ? [{token: 'job', value: jobNames[0]}] : [],
    );
    return (
      <Warning>
        <span>
          {`${jobNamesSummary} ran `}
          <Link to={jobsPage}>{count} times</Link> but did not materialize this asset
        </span>
      </Warning>
    );
  }
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
