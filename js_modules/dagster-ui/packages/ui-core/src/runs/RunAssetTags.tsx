import {useMemo} from 'react';

import {AssetKeyTagCollection} from './AssetTagCollections';
import {gql, useQuery} from '../apollo-client';
import {RunAssetsQuery, RunAssetsQueryVariables} from './types/RunAssetTags.types';
import {RunFragment} from './types/RunFragments.types';

export const RunAssetTags = (props: {run: RunFragment}) => {
  const {run} = props;
  const queryResult = useQuery<RunAssetsQuery, RunAssetsQueryVariables>(RUN_ASSETS_QUERY, {
    variables: {runId: run.id},
    fetchPolicy: 'no-cache',
  });

  const assetKeys = useMemo(() => {
    const {data, loading} = queryResult;
    if (loading || !data || data.pipelineRunOrError.__typename !== 'Run') {
      return null;
    }

    return data.pipelineRunOrError.assets.map((a) => a.key);
  }, [queryResult]);

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
