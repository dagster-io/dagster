import {Box, NonIdealState} from '@dagster-io/ui-components';
import {useParams} from 'react-router-dom';

import {AssetJobPartitionsView} from './AssetJobPartitionsView';
import {OpJobPartitionsView} from './OpJobPartitionsView';
import {usePartitionNameForPipeline} from '../assets/usePartitionNameForPipeline';
import {explorerPathFromString, useStripSnapshotFromPath} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {LoadingSpinner} from '../ui/Loading';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelinePartitionsRoot = (props: Props) => {
  const {repoAddress} = props;
  const params = useParams<{pipelinePath: string}>();
  const {pipelinePath} = params;

  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const pipelineInfo = repo?.repository.pipelines.find(
    (pipelineOrJob) => pipelineOrJob.name === pipelineName,
  );
  const isJob = !!pipelineInfo?.isJob;
  const isAssetJob = !!pipelineInfo?.isAssetJob;

  useJobTitle(explorerPath, isJob);
  useStripSnapshotFromPath(params);

  const {partitionSet, partitionSetError} = usePartitionNameForPipeline(repoAddress, pipelineName);

  if (!partitionSet && !partitionSetError) {
    return <LoadingSpinner purpose="page" />;
  }
  if (partitionSetError) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState icon="error" title="Partitions" description={partitionSetError.message} />
      </Box>
    );
  }

  if (!partitionSet) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="error"
          title="Partitions"
          description={
            <div>
              There are no partition sets defined for {isJob ? 'job' : 'pipeline'}{' '}
              <code>{pipelineName}</code>.
            </div>
          }
        />
      </Box>
    );
  }

  return isAssetJob ? (
    <AssetJobPartitionsView
      pipelineName={pipelineName}
      partitionSetName={partitionSet.name}
      repoAddress={repoAddress}
    />
  ) : (
    <OpJobPartitionsView partitionSetName={partitionSet.name} repoAddress={repoAddress} />
  );
};
