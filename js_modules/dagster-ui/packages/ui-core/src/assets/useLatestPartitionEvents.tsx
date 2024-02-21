import {gql, useQuery} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import React from 'react';

import {asAssetKeyInput} from './asInput';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';
import {
  AssetOverviewMetadataEventsQuery,
  AssetOverviewMetadataEventsQueryVariables,
} from './types/useLatestPartitionEvents.types';
import {LiveDataForNode} from '../asset-graph/Utils';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';

export function useLatestPartitionEvents(
  assetNode: AssetNodeDefinitionFragment,
  assetNodeLoadTimestamp: number | undefined,
  liveData: LiveDataForNode | undefined,
) {
  const refreshHint = liveData?.lastMaterialization?.timestamp;

  const {data, refetch} = useQuery<
    AssetOverviewMetadataEventsQuery,
    AssetOverviewMetadataEventsQueryVariables
  >(ASSET_OVERVIEW_METADATA_EVENTS_QUERY, {
    variables: {assetKey: asAssetKeyInput(assetNode)},
  });

  React.useEffect(() => {
    refetch();
  }, [refetch, refreshHint, assetNodeLoadTimestamp]);

  const materialization =
    data?.assetOrError.__typename === 'Asset'
      ? data.assetOrError.assetMaterializations[0]
      : undefined;
  const observation =
    data?.assetOrError.__typename === 'Asset' ? data.assetOrError.assetObservations[0] : undefined;

  return {materialization, observation};
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
