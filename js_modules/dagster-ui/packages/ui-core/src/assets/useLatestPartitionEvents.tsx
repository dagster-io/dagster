// eslint-disable-next-line no-restricted-imports
import React from 'react';

import {AssetKey} from './types';
import {gql, useQuery} from '../apollo-client';
import {
  AssetOverviewMetadataEventsQuery,
  AssetOverviewMetadataEventsQueryVariables,
} from './types/useLatestPartitionEvents.types';
import {LiveDataForNode} from '../asset-graph/Utils';
import {usePredicateChangeSignal} from '../hooks/usePredicateChangeSignal';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntryFragment';

export function useLatestPartitionEvents(
  assetKey: AssetKey,
  assetNodeLoadTimestamp: number | undefined,
  liveData: LiveDataForNode | undefined,
) {
  const lastMaterializationTimestamp = liveData?.lastMaterialization?.timestamp;

  const queryResult = useQuery<
    AssetOverviewMetadataEventsQuery,
    AssetOverviewMetadataEventsQueryVariables
  >(ASSET_OVERVIEW_METADATA_EVENTS_QUERY, {
    variables: {assetKey: {path: assetKey.path}},
  });

  const {data, refetch} = queryResult;

  const refreshHint = usePredicateChangeSignal(
    (prevHints, [lastMaterializationTimestamp, assetNodeLoadTimestamp]) => {
      const [prevLastMaterializationTimestamp, prevAssetNodeLoadTimestamp] =
        prevHints || ([undefined, undefined] as const);

      return !!(
        /**
         * Trigger a refetch only if a previous a timestamp hint existed and has changed.
         * This avoids redundant queries since these timestamps are fetched in parallel.
         */
        (
          (prevLastMaterializationTimestamp &&
            lastMaterializationTimestamp !== prevLastMaterializationTimestamp) ||
          (prevAssetNodeLoadTimestamp && prevAssetNodeLoadTimestamp !== assetNodeLoadTimestamp)
        )
      );
    },
    [lastMaterializationTimestamp, assetNodeLoadTimestamp],
  );

  React.useEffect(() => {
    refetch();
  }, [refetch, refreshHint]);

  const materialization =
    data?.assetOrError.__typename === 'Asset'
      ? data.assetOrError.assetMaterializations[0]
      : undefined;
  const observation =
    data?.assetOrError.__typename === 'Asset' ? data.assetOrError.assetObservations[0] : undefined;

  return {materialization, observation, loading: !data};
}

export const ASSET_OVERVIEW_METADATA_EVENTS_QUERY = gql`
  query AssetOverviewMetadataEventsQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        assetMaterializations(limit: 1, partitionInLast: 1) {
          timestamp
          runId
          metadataEntries {
            ...MetadataEntryFragment
          }
        }
        assetObservations(limit: 1, partitionInLast: 1) {
          timestamp
          runId
          metadataEntries {
            ...MetadataEntryFragment
          }
        }
      }
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
`;
