import {useMemo} from 'react';

import {AssetCheckTagCollection} from './AssetTagCollections';
import {gql, useQuery} from '../apollo-client';
import {RunAssetChecksQuery, RunAssetChecksQueryVariables} from './types/RunAssetCheckTags.types';
import {RunFragment} from './types/RunFragments.types';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';

export const RunAssetCheckTags = (props: {
  run: Pick<RunFragment, 'id' | 'pipelineName' | 'assetCheckSelection'>;
}) => {
  const {run} = props;

  // For a hidden asset group job with an explicit (non-empty) asset check selection, that selection
  // is the authoritative set of targeted checks, so use it directly and skip the query. Otherwise -
  // a non-hidden job, or a null/empty selection (which means "every check on the targeted assets") -
  // the query resolves the concrete set from the run's execution plan and any runtime evaluations.
  const skip = isHiddenAssetGroupJob(run.pipelineName) && !!run.assetCheckSelection?.length;

  const queryResult = useQuery<RunAssetChecksQuery, RunAssetChecksQueryVariables>(
    RUN_ASSETS_CHECKS_QUERY,
    {
      variables: {runId: run.id},
      skip,
    },
  );

  const assetChecks = useMemo(() => {
    if (skip) {
      return run.assetCheckSelection;
    }
    const {data} = queryResult;
    if (data?.pipelineRunOrError.__typename === 'Run') {
      return data.pipelineRunOrError.assetChecks;
    }
    return null;
  }, [queryResult, run, skip]);

  return <AssetCheckTagCollection assetChecks={assetChecks} />;
};

export const RUN_ASSETS_CHECKS_QUERY = gql`
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
