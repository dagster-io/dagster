import {AssetKeyTagCollection} from './AssetTagCollections';
import {assetKeysForRun} from './RunUtils';
import {RunAssetsQuery, RunAssetsQueryVariables} from './types/RunAssetTags.types';
import {RunFragment} from './types/RunFragments.types';
import {gql, useQuery} from '../apollo-client';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

export const RunAssetTags = (props: {run: RunFragment}) => {
  const {run} = props;
  const skip = isHiddenAssetGroupJob(run.pipelineName);
  const queryResult = useQuery<RunAssetsQuery, RunAssetsQueryVariables>(RUN_ASSETS_QUERY, {
    variables: {runId: run.id},
    skip,
    fetchPolicy: 'no-cache',
  });
  const {data, loading} = queryResult;

  if (loading || !data || data.pipelineRunOrError.__typename !== 'Run') {
    return null;
  }

  const assetKeys = skip ? assetKeysForRun(run) : data.pipelineRunOrError.assets.map((a) => a.key);

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
