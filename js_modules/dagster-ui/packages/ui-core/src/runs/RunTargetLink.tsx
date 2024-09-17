import {Box} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetCheckTagCollection, AssetKeyTagCollection} from './AssetTagCollections';
import {assetKeysForRun} from './RunUtils';
import {RunTableRunFragment} from './types/RunTableRunFragment.types';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RepoAddress} from '../workspace/types';

export const RunTargetLink = ({
  run,
  isJob,
  repoAddress,
}: {
  isJob: boolean;
  run: Pick<
    RunTableRunFragment,
    'pipelineName' | 'assetSelection' | 'stepKeysToExecute' | 'assetCheckSelection'
  >;
  repoAddress: RepoAddress | null;
}) => {
  return isHiddenAssetGroupJob(run.pipelineName) ? (
    <Box flex={{gap: 16, alignItems: 'end', wrap: 'wrap'}}>
      <AssetKeyTagCollection assetKeys={assetKeysForRun(run)} />
      <AssetCheckTagCollection assetChecks={run.assetCheckSelection} />
    </Box>
  ) : (
    <PipelineReference
      isJob={isJob}
      showIcon
      pipelineName={run.pipelineName}
      pipelineHrefContext={repoAddress || 'repo-unknown'}
    />
  );
};
