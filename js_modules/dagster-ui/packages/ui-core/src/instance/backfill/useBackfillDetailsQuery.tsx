import {gql, useQuery} from '@apollo/client';

import {BACKFILL_ACTIONS_BACKFILL_FRAGMENT} from './BackfillActionsMenu';
import {
  BackfillStatusesByAssetQuery,
  BackfillStatusesByAssetQueryVariables,
} from './types/BackfillPage.types';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {useBlockTraceOnQueryResult} from '../../performance/TraceContext';

export function useBackfillDetailsQuery(backfillId: string) {
  const queryResult = useQuery<BackfillStatusesByAssetQuery, BackfillStatusesByAssetQueryVariables>(
    BACKFILL_DETAILS_QUERY,
    {variables: {backfillId}},
  );
  useBlockTraceOnQueryResult(queryResult, 'BackfillStatusesByAssetQuery');
  return queryResult;
}

export const BACKFILL_DETAILS_QUERY = gql`
  query BackfillStatusesByAsset($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ...BackfillDetailsBackfillFragment
      ...PythonErrorFragment
      ... on BackfillNotFoundError {
        message
      }
    }
  }

  fragment BackfillDetailsBackfillFragment on PartitionBackfill {
    id
    status
    timestamp
    endTimestamp
    numPartitions
    ...BackfillActionsBackfillFragment

    error {
      ...PythonErrorFragment
    }
    assetBackfillData {
      rootTargetedPartitions {
        partitionKeys
        ranges {
          start
          end
        }
      }
      assetBackfillStatuses {
        ... on AssetPartitionsStatusCounts {
          assetKey {
            path
          }
          numPartitionsTargeted
          numPartitionsInProgress
          numPartitionsMaterialized
          numPartitionsFailed
        }
        ... on UnpartitionedAssetStatus {
          assetKey {
            path
          }
          inProgress
          materialized
          failed
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${BACKFILL_ACTIONS_BACKFILL_FRAGMENT}
`;
