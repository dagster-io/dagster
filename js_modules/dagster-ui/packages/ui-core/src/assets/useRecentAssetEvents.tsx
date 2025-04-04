import uniq from 'lodash/uniq';
import {useMemo} from 'react';

import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetKey, AssetViewParams} from './types';
import {gql, useQuery} from '../apollo-client';
import {clipEventsToSharedMinimumTime} from './clipEventsToSharedMinimumTime';
import {MaterializationHistoryEventTypeSelector} from '../graphql/types';
import {
  AssetEventsQuery,
  AssetEventsQueryVariables,
  AssetFailedToMaterializeFragment,
  AssetSuccessfulMaterializationFragment,
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

/**
 * If the asset has a defined partition space, we load all materializations in the
 * last 100 partitions. This ensures that if you run a huge backfill of old partitions,
 * you still see accurate info for the last 100 partitions in the UI. A count-based
 * limit could cause random partitions to disappear if materializations were out of order.
 */
export function useRecentAssetEvents(
  assetKey: AssetKey | undefined,
  params: Pick<AssetViewParams, 'asOf' | 'partition' | 'time'> & {
    partitionKeys?: string[];
  },
  {assetHasDefinedPartitions}: {assetHasDefinedPartitions: boolean},
) {
  const before = params.asOf ? `${Number(params.asOf) + 1}` : undefined;
  const xAxis = getXAxisForParams(params, {defaultToPartitions: assetHasDefinedPartitions});

  const loadUsingPartitionKeys = assetHasDefinedPartitions && xAxis === 'partition';

  const queryResult = useQuery<AssetEventsQuery, AssetEventsQueryVariables>(ASSET_EVENTS_QUERY, {
    skip: !assetKey,
    fetchPolicy: 'cache-and-network',
    variables: loadUsingPartitionKeys
      ? {
          assetKey: {path: assetKey?.path ?? []},
          before,
          partitionInLast: 120,
          eventTypeSelector: MaterializationHistoryEventTypeSelector.ALL,
        }
      : {
          assetKey: {path: assetKey?.path ?? []},
          before,
          limit: 100,
          eventTypeSelector: MaterializationHistoryEventTypeSelector.ALL,
        },
  });
  const {data, loading, refetch} = queryResult;

  const value = useMemo(() => {
    const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;

    const loaded = {
      materializations: asset?.assetMaterializationHistory?.results || [],
      observations: asset?.assetObservations.results || [],
    };

    const {materializations, observations} = !loadUsingPartitionKeys
      ? clipEventsToSharedMinimumTime(loaded.materializations, loaded.observations, 100)
      : loaded;

    const allPartitionKeys = asset?.definition?.partitionKeys;
    const loadedPartitionKeys: string[] =
      loadUsingPartitionKeys && allPartitionKeys
        ? allPartitionKeys.slice(allPartitionKeys.length - 120)
        : uniq(
            [...materializations, ...observations].map((o) => o.partition!).filter(Boolean),
          ).sort();

    return {
      asset,
      loadedPartitionKeys,
      materializations,
      observations,
      loading,
      refetch,
      xAxis,
    };
  }, [data, loading, refetch, loadUsingPartitionKeys, xAxis]);

  return value;
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
          results {
            ...AssetObservationFragment
          }
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
