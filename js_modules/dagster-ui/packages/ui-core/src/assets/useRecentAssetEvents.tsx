import {useMemo} from 'react';

import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetKey, AssetViewParams} from './types';
import {gql, useQuery} from '../apollo-client';
import {clipEventsToSharedMinimumTime} from './clipEventsToSharedMinimumTime';
import {MaterializationHistoryEventTypeSelector} from '../graphql/types';
import {
  AssetFailedToMaterializeFragment,
  AssetPartitionEventsQuery,
  AssetPartitionEventsQueryVariables,
  AssetSuccessfulMaterializationFragment,
  LatestAssetPartitionsQuery,
  LatestAssetPartitionsQueryVariables,
  RecentAssetEventsQuery,
  RecentAssetEventsQueryVariables,
} from './types/useRecentAssetEvents.types';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntryFragment';

export type AssetMaterializationFragment =
  | AssetSuccessfulMaterializationFragment
  | AssetFailedToMaterializeFragment;

/**
The params behavior on this page is a bit nuanced - there are two main query
params: ?timestamp= and ?partition= and only one is set at a time. They can
be undefined, an empty string or a value and all three states are used.
- If both are undefined, we expand the first item in the table by default
- If one is present, it determines which xAxis is used (partition grouping)
- If one is present and set to a value, that item in the table is expanded.
- If one is present but an empty string, no items in the table is expanded.
 */
export function getXAxisForParams(
  params: Pick<AssetViewParams, 'asOf' | 'partition' | 'time'>,
  {defaultToPartitions}: {defaultToPartitions: boolean},
) {
  const xAxisDefault = defaultToPartitions ? 'partition' : 'time';
  const xAxis: 'partition' | 'time' =
    params.partition !== undefined
      ? 'partition'
      : params.time !== undefined || params.asOf
        ? 'time'
        : xAxisDefault;
  return xAxis;
}

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
  eventTypeSelector: MaterializationHistoryEventTypeSelector,
) {
  const queryResult = useQuery<RecentAssetEventsQuery, RecentAssetEventsQueryVariables>(
    RECENT_ASSET_EVENTS_QUERY,
    {
      skip: !assetKey,
      fetchPolicy: 'cache-and-network',
      variables: {
        assetKey: {path: assetKey?.path || []},
        limit,
        eventTypeSelector: eventTypeSelector || MaterializationHistoryEventTypeSelector.ALL,
      },
    },
  );
  const {data, loading, refetch} = queryResult;

  const value = useMemo(() => {
    const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;
    const {materializations, observations} = clipEventsToSharedMinimumTime(
      asset?.assetMaterializationHistory?.results || [],
      asset?.assetObservations || [],
      limit,
    );

    return {
      materializations,
      observations,
      loading,
      refetch,
    };
  }, [data, loading, refetch, limit]);

  return value;
}

export function useAssetPartitionMaterializations(
  assetKey: AssetKey | undefined,
  partitionKeys: string[],
) {
  const queryResult = useQuery<AssetPartitionEventsQuery, AssetPartitionEventsQueryVariables>(
    ASSET_PARTITIONS_MATERIALIZATIONS_QUERY,
    {
      skip: !assetKey,
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
  const {partitionKeys} = useLatestAssetPartitions(assetKey, limit);
  return useAssetPartitionMaterializations(assetKey, [...partitionKeys].reverse());
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
    $eventTypeSelector: MaterializationHistoryEventTypeSelector!
    $limit: Int
    $before: String
    $after: String
    $cursor: String
  ) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetObservations(
          limit: $limit
          beforeTimestampMillis: $before
          afterTimestampMillis: $after
        ) {
          ...AssetObservationFragment
        }
        assetMaterializationHistory(
          limit: $limit
          afterTimestampMillis: $after
          beforeTimestampMillis: $before
          eventTypeSelector: $eventTypeSelector
          cursor: $cursor
        ) {
          results {
            ...AssetSuccessfulMaterializationFragment
            ...AssetFailedToMaterializeFragment
          }
          cursor
        }
      }
    }
  }

  ${ASSET_OBSERVATION_FRAGMENT}
  ${ASSET_SUCCESSFUL_MATERIALIZATION_FRAGMENT}
  ${ASSET_FAILED_TO_MATERIALIZE_FRAGMENT}
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

export const ASSET_EVENTS_QUERY = gql`
  query AssetEventsQuery(
    $assetKey: AssetKeyInput!
    $limit: Int
    $before: String
    $after: String
    $partitionInLast: Int
    $eventTypeSelector: MaterializationHistoryEventTypeSelector!
    $partitions: [String!]
    $cursor: String
  ) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetObservations(
          limit: $limit
          beforeTimestampMillis: $before
          afterTimestampMillis: $after
          partitionInLast: $partitionInLast
          partitions: $partitions
        ) {
          ...AssetObservationFragment
        }
        assetMaterializationHistory(
          limit: $limit
          beforeTimestampMillis: $before
          afterTimestampMillis: $after
          partitionInLast: $partitionInLast
          eventTypeSelector: $eventTypeSelector
          partitions: $partitions
          cursor: $cursor
        ) {
          results {
            ...AssetSuccessfulMaterializationFragment
            ...AssetFailedToMaterializeFragment
          }
          cursor
        }
        definition {
          id
          partitionKeys
        }
      }
    }
  }
  ${ASSET_OBSERVATION_FRAGMENT}
  ${ASSET_SUCCESSFUL_MATERIALIZATION_FRAGMENT}
  ${ASSET_FAILED_TO_MATERIALIZE_FRAGMENT}
`;
