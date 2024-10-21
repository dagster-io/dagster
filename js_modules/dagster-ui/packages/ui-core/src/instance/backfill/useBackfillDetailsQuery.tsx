import {BACKFILL_ACTIONS_BACKFILL_FRAGMENT} from './BackfillFragments';
import {
  BackfillDetailsQuery,
  BackfillDetailsQueryVariables,
} from './types/useBackfillDetailsQuery.types';
import {gql, useQuery} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
export function useBackfillDetailsQuery(backfillId: string) {
  const queryResult = useQuery<BackfillDetailsQuery, BackfillDetailsQueryVariables>(
    BACKFILL_DETAILS_QUERY,
    {variables: {backfillId}},
  );
  return queryResult;
}

export const JOB_BACKFILL_DETAILS_FRAGMENT = gql`
  fragment JobBackfillDetailsFragment on PartitionStatuses {
    results {
      id
      partitionName
      runId
      runStatus
      runDuration
    }
  }
`;
export const ASSET_BACKFILL_DETAILS_FRAGMENT = gql`
  fragment AssetBackfillDetailsFragment on AssetBackfillData {
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
`;

export const BACKFILL_DETAILS_QUERY = gql`
  query BackfillDetailsQuery($backfillId: String!) {
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
    isAssetBackfill
    assetSelection {
      path
    }
    partitionSetName

    error {
      ...PythonErrorFragment
    }
    assetBackfillData {
      ...AssetBackfillDetailsFragment
    }
    partitionStatuses {
      ...JobBackfillDetailsFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${BACKFILL_ACTIONS_BACKFILL_FRAGMENT}
  ${ASSET_BACKFILL_DETAILS_FRAGMENT}
  ${JOB_BACKFILL_DETAILS_FRAGMENT}
`;
