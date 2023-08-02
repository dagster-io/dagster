import {Box} from '@dagster-io/ui-components';
import * as React from 'react';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

export const SensorTargetList: React.FC<{
  targets: {pipelineName: string}[] | null | undefined;
  repoAddress: RepoAddress;
}> = ({targets, repoAddress}) => {
  const repo = useRepository(repoAddress);
  if (!targets) {
    return <span />;
  }

  const visibleTargets = targets.filter((target) => !isHiddenAssetGroupJob(target.pipelineName));

  return (
    <Box flex={{direction: 'column', gap: 2}}>
      {visibleTargets.length < targets.length && <span>A selection of assets</span>}
      {visibleTargets.map((target) =>
        target.pipelineName ? (
          <PipelineReference
            key={target.pipelineName}
            pipelineName={target.pipelineName}
            pipelineHrefContext={repoAddress}
            isJob={!!(repo && isThisThingAJob(repo, target.pipelineName))}
          />
        ) : null,
      )}
    </Box>
  );
};
