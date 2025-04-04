import {Box} from '@dagster-io/ui-components';
import * as React from 'react';

import {AssetCheckTagCollection, AssetKeyTagCollection} from './AssetTagCollections';
import {assetKeysForRun} from './RunUtils';
import {RunTableRunFragment} from './types/RunTableRunFragment.types';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PipelineTag} from '../pipelines/PipelineReference';
import {RepoAddress} from '../workspace/types';

export const RunTargetLink = ({
  run,
  repoAddress,
  extraTags,
}: {
  run: Pick<
    RunTableRunFragment,
    'pipelineName' | 'assetSelection' | 'stepKeysToExecute' | 'assetCheckSelection'
  >;
  repoAddress: RepoAddress | null;
  extraTags?: React.ReactNode[];
}) => {
  const assetKeys = React.useMemo(() => {
    return isHiddenAssetGroupJob(run.pipelineName) ? assetKeysForRun(run) : null;
  }, [run]);

  if (assetKeys) {
    return (
      <Box flex={{direction: 'column', gap: 4}}>
        <AssetKeyTagCollection
          assetKeys={assetKeys}
          useTags
          extraTags={extraTags}
          maxRows={run.assetCheckSelection?.length ? 1 : 2}
        />
        <AssetCheckTagCollection
          assetChecks={run.assetCheckSelection}
          maxRows={assetKeys?.length ? 1 : 2}
        />
      </Box>
    );
  }
  return (
    <PipelineTag
      isJob
      showIcon
      pipelineName={run.pipelineName}
      pipelineHrefContext={repoAddress || 'repo-unknown'}
    />
  );
};
