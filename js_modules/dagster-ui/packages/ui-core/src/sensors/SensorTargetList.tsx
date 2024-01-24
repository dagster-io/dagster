import {Box} from '@dagster-io/ui-components';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

export const SensorTargetList = ({
  targets,
  repoAddress,
}: {
  targets: {pipelineName: string}[] | null | undefined;
  repoAddress: RepoAddress;
}) => {
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
