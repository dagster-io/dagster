import {useMemo} from 'react';

import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetKey} from './types';
import {gql, useQuery} from '../apollo-client';
import {ASSET_LATEST_INFO_FRAGMENT} from '../asset-data/AssetBaseDataProvider';
import {
  AssetFailedToMaterializeFragment,
  AssetObservationFragment,
  AssetPartitionEventsQuery,
  AssetPartitionEventsQueryVariables,
  AssetSuccessfulMaterializationFragment,
  LatestAssetPartitionsQuery,
  LatestAssetPartitionsQueryVariables,
  RecentAssetEventsForCatalogViewQuery,
  RecentAssetEventsForCatalogViewQueryVariables,
  RecentAssetEventsQuery,
  RecentAssetEventsQueryVariables,
} from './types/useRecentAssetEvents.types';
import {AssetEventHistoryEventTypeSelector} from '../graphql/types';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntryFragment';

export type AssetEventFragment =
  | AssetSuccessfulMaterializationFragment
  | AssetFailedToMaterializeFragment
  | AssetObservationFragment;

export function useLatestAssetPartitions(assetKey: AssetKey | undefined, limit: number) {
  const queryResult = useQuery<LatestAssetPartitionsQuery, LatestAssetPartitionsQueryVariables>(
    LATEST_ASSET_PARTITIONS_QUERY,
    {
      skip: !assetKey,
      fetchPolicy: 'cache-and-network',
      variables: {
        assetKey: {path: assetKey ? assetKey.path : []},
        limit,
      },
    },
  );

  const {data, loading, refetch} = queryResult;
  const value = useMemo(() => {
    const assetNode =
      data?.assetNodeOrError.__typename === 'AssetNode' ? data?.assetNodeOrError : null;
    const partitionKeys = assetNode?.partitionKeyConnection?.results || [];

    return {
      partitionKeys,
      loading,
      refetch,
    };
  }, [data, loading, refetch]);
  return value;
}

export function useRecentAssetEvents(
  assetKey: AssetKey | undefined,
  limit: number,
  eventTypeSelectors: AssetEventHistoryEventTypeSelector[],
) {
  const queryResult = useQuery<RecentAssetEventsQuery, RecentAssetEventsQueryVariables>(
    RECENT_ASSET_EVENTS_QUERY,
    {
      skip: !assetKey,
      fetchPolicy: 'cache-and-network',
      variables: {
        assetKey: {path: assetKey?.path || []},
        limit,
        eventTypeSelectors: eventTypeSelectors || [
          AssetEventHistoryEventTypeSelector.MATERIALIZATION,
          AssetEventHistoryEventTypeSelector.OBSERVATION,
          AssetEventHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
        ],
      },
    },
  );
  const {data, loading, refetch} = queryResult;

  const value = useMemo(() => {
    const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;

    return {
      latestInfo: data?.assetsLatestInfo[0],
      events: asset?.assetEventHistory?.results || [],
      loading: loading && !data,
      refetch,
    };
  }, [data, loading, refetch]);

  return value;
}

export function useRecentAssetEventsForCatalogView({
  assetKey,
  limit,
  eventTypeSelectors,
}: {
  assetKey: AssetKey | undefined;
  limit: number;
  eventTypeSelectors: AssetEventHistoryEventTypeSelector[];
}) {
  const queryResult = useQuery<
    RecentAssetEventsForCatalogViewQuery,
    RecentAssetEventsForCatalogViewQueryVariables
  >(RECENT_ASSET_EVENTS_QUERY_FOR_CATALOG_VIEW, {
    skip: !assetKey,
    fetchPolicy: 'cache-and-network',
    variables: {
      assetKey: {path: assetKey?.path || []},
      limit,
      eventTypeSelectors,
    },
  });
  const {data, loading, refetch} = queryResult;

  const value = useMemo(() => {
    const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;

    return {
      latestInfo: data?.assetsLatestInfo[0],
      events: asset?.assetEventHistory?.results || [],
      loading: loading && !data,
      refetch,
    };
  }, [data, loading, refetch]);

  return value;
}

export function useAssetPartitionMaterializations(
  assetKey: AssetKey | undefined,
  partitionKeys: string[],
  loadingPartitions: boolean,
) {
  const queryResult = useQuery<AssetPartitionEventsQuery, AssetPartitionEventsQueryVariables>(
    ASSET_PARTITIONS_MATERIALIZATIONS_QUERY,
    {
      skip: !assetKey || loadingPartitions,
      fetchPolicy: 'cache-and-network',
      variables: {
        assetKey: {path: assetKey ? assetKey.path : []},
        partitions: partitionKeys,
      },
    },
  );

  const {data, loading, refetch} = queryResult;

  const value = useMemo(() => {
    const assetNode =
      data?.assetNodeOrError.__typename === 'AssetNode' ? data?.assetNodeOrError : null;
    const materializations = (assetNode?.latestMaterializationByPartition || []).filter(
      (event) => event !== null,
    );

    return {
      materializations,
      partitionKeys,
      loading,
      refetch,
    };
  }, [data, loading, refetch, partitionKeys]);

  return value;
}

export function useLatestAssetPartitionMaterializations(
  assetKey: AssetKey | undefined,
  limit: number,
) {
  const {partitionKeys, loading} = useLatestAssetPartitions(assetKey, limit);
  return useAssetPartitionMaterializations(
    assetKey,
    useMemo(() => [...partitionKeys].reverse(), [partitionKeys]),
    loading,
  );
}

export type RecentAssetEvents = ReturnType<typeof useRecentAssetEvents>;

export const ASSET_FAILED_TO_MATERIALIZE_FRAGMENT = gql`
  fragment AssetFailedToMaterializeFragment on FailedToMaterializeEvent {
    tags {
      key
      value
    }
    runOrError {
      ... on PipelineRun {
        id
        mode
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
        status
        pipelineName
        pipelineSnapshotId
      }
    }
    runId
    timestamp
    stepKey
    label
    description
    assetKey {
      path
    }
    partition
    metadataEntries {
      ...MetadataEntryFragment
    }
    materializationFailureType
  }

  ${METADATA_ENTRY_FRAGMENT}
  ${ASSET_LINEAGE_FRAGMENT}
`;

export const ASSET_SUCCESSFUL_MATERIALIZATION_FRAGMENT = gql`
  fragment AssetSuccessfulMaterializationFragment on MaterializationEvent {
    partition
    tags {
      key
      value
    }
    runOrError {
      ... on PipelineRun {
        id
        mode
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
        status
        pipelineName
        pipelineSnapshotId
      }
    }
    runId
    timestamp
    stepKey
    label
    description
    metadataEntries {
      ...MetadataEntryFragment
    }
    assetLineage {
      ...AssetLineageFragment
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
  ${ASSET_LINEAGE_FRAGMENT}
`;

export const ASSET_OBSERVATION_FRAGMENT = gql`
  fragment AssetObservationFragment on ObservationEvent {
    partition
    tags {
      key
      value
    }
    runOrError {
      ... on PipelineRun {
        id
        mode
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
        status
        pipelineName
        pipelineSnapshotId
      }
    }
    runId
    timestamp
    stepKey
    label
    description
    metadataEntries {
      ...MetadataEntryFragment
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
`;

export const RECENT_ASSET_EVENTS_QUERY = gql`
  query RecentAssetEventsQuery(
    $assetKey: AssetKeyInput!
    $eventTypeSelectors: [AssetEventHistoryEventTypeSelector!]!
    $limit: Int!
    $before: String
    $after: String
    $cursor: String
    $partitions: [String!]
  ) {
    assetsLatestInfo(assetKeys: [$assetKey]) {
      id
      ...AssetLatestInfoFragment
    }
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetEventHistory(
          limit: $limit
          afterTimestampMillis: $after
          beforeTimestampMillis: $before
          eventTypeSelectors: $eventTypeSelectors
          cursor: $cursor
          partitions: $partitions
        ) {
          results {
            ...AssetSuccessfulMaterializationFragment
            ...AssetFailedToMaterializeFragment
            ...AssetObservationFragment
          }
          cursor
        }
      }
    }
  }

  ${ASSET_OBSERVATION_FRAGMENT}
  ${ASSET_SUCCESSFUL_MATERIALIZATION_FRAGMENT}
  ${ASSET_FAILED_TO_MATERIALIZE_FRAGMENT}
  ${ASSET_LATEST_INFO_FRAGMENT}
`;

export const RECENT_ASSET_EVENTS_QUERY_FOR_CATALOG_VIEW = gql`
  query RecentAssetEventsForCatalogViewQuery(
    $assetKey: AssetKeyInput!
    $eventTypeSelectors: [AssetEventHistoryEventTypeSelector!]!
    $limit: Int!
    $before: String
    $after: String
    $cursor: String
    $partitions: [String!]
  ) {
    assetsLatestInfo(assetKeys: [$assetKey]) {
      id
      latestRun {
        id
        status
        startTime
      }
      inProgressRunIds
      unstartedRunIds
    }
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetEventHistory(
          limit: $limit
          afterTimestampMillis: $after
          beforeTimestampMillis: $before
          eventTypeSelectors: $eventTypeSelectors
          cursor: $cursor
          partitions: $partitions
        ) {
          results {
            ... on MaterializationEvent {
              runId
              timestamp
            }
            ... on FailedToMaterializeEvent {
              runId
              timestamp
            }
            ... on ObservationEvent {
              runId
              timestamp
            }
          }
          cursor
        }
      }
    }
  }
`;

export const ASSET_PARTITIONS_MATERIALIZATIONS_QUERY = gql`
  query AssetPartitionEventsQuery($assetKey: AssetKeyInput!, $partitions: [String!]!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        latestMaterializationByPartition(partitions: $partitions) {
          ...AssetSuccessfulMaterializationFragment
        }
      }
    }
  }

  ${ASSET_SUCCESSFUL_MATERIALIZATION_FRAGMENT}
`;

export const LATEST_ASSET_PARTITIONS_QUERY = gql`
  query LatestAssetPartitionsQuery($assetKey: AssetKeyInput!, $limit: Int!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        partitionKeyConnection(limit: $limit, ascending: false) {
          results
        }
      }
    }
  }
`;
