import {AssetCheckTagCollection} from './AssetTagCollections';
import {RunAssetChecksQuery, RunAssetChecksQueryVariables} from './types/RunAssetCheckTags.types';
import {RunFragment} from './types/RunFragments.types';
import {gql, useQuery} from '../apollo-client';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

export const RunAssetCheckTags = (props: {run: RunFragment}) => {
  const {run} = props;
  const skip = isHiddenAssetGroupJob(run.pipelineName);
  const queryResult = useQuery<RunAssetChecksQuery, RunAssetChecksQueryVariables>(
    RUN_ASSETS_CHECKS_QUERY,
    {
      variables: {runId: run.id},
      skip,
    },
  );
  const {data, loading} = queryResult;

  if (loading || !data || data.pipelineRunOrError.__typename !== 'Run') {
    return null;
  }

  const assetChecks = skip ? run.assetCheckSelection : data.pipelineRunOrError.assetChecks;

  return <AssetCheckTagCollection useTags assetChecks={assetChecks} />;
};

const RUN_ASSETS_CHECKS_QUERY = gql`
  query RunAssetChecksQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        assetChecks {
          name
          assetKey {
            path
          }
        }
      }
    }
  }
`;
