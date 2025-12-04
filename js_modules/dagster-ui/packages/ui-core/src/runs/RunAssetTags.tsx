import {useMemo} from 'react';

import {AssetKeyTagCollection} from './AssetTagCollections';
import {assetKeysForRun} from './RunUtils';
import {gql, useQuery} from '../apollo-client';
import {RunAssetsQuery, RunAssetsQueryVariables} from './types/RunAssetTags.types';
import {RunFragment} from './types/RunFragments.types';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

export const RunAssetTags = (props: {
  run: Pick<RunFragment, 'id' | 'stepKeysToExecute' | 'pipelineName' | 'assetSelection'>;
}) => {
  const {run} = props;
  const skip = isHiddenAssetGroupJob(run.pipelineName);
  const queryResult = useQuery<RunAssetsQuery, RunAssetsQueryVariables>(RUN_ASSETS_QUERY, {
    variables: {runId: run.id},
    skip,
    fetchPolicy: 'no-cache',
  });

  const assetKeys = useMemo(() => {
    const {data} = queryResult;
    let keys = null;
    if (data?.pipelineRunOrError.__typename === 'Run') {
      keys = data.pipelineRunOrError.assets.map((a) => a.key);
    }

    return skip ? assetKeysForRun(run) : keys;
  }, [queryResult, run, skip]);

  return <AssetKeyTagCollection useTags assetKeys={assetKeys} />;
};

const RUN_ASSETS_QUERY = gql`
  query RunAssetsQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        assets {
          id
          key {
            path
          }
        }
      }
    }
  }
`;
