import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';

import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetViewParams} from './AssetView';
import {AssetKey} from './types';
import {AssetEventsQuery, AssetEventsQueryVariables} from './types/AssetEventsQuery';

/**
 * If the asset has a defined partition space, we load all materializations in the
 * last 100 partitions. This ensures that if you run a huge backfill of old partitions,
 * you still see accurate info for the last 100 partitions in the UI. A count-based
 * limit could cause random partitions to disappear if materializations were out of order.
 */
export function useRecentAssetEvents(
  assetKey: AssetKey,
  assetHasDefinedPartitions: boolean,
  params: AssetViewParams,
) {
  // The params behavior on this page is a bit nuanced - there are two main query
  // params: ?timestamp= and ?partition= and only one is set at a time. They can
  // be undefined, an empty string or a value and all three states are used.
  //
  // - If both are undefined, we expand the first item in the table by default
  // - If one is present, it determines which xAxis is used (partition grouping)
  // - If one is present and set to a value, that item in the table is expanded.
  // - If one is present but an empty string, no items in the table is expanded.

  const before = params.asOf ? `${Number(params.asOf) + 1}` : undefined;
  const xAxisDefault = assetHasDefinedPartitions ? 'partition' : 'time';
  const xAxis: 'partition' | 'time' =
    assetHasDefinedPartitions && params.partition !== undefined
      ? 'partition'
      : params.time !== undefined || before
      ? 'time'
      : xAxisDefault;

  const loadUsingPartitionKeys = assetHasDefinedPartitions && xAxis === 'partition';

  const {data, loading, refetch} = useQuery<AssetEventsQuery, AssetEventsQueryVariables>(
    ASSET_EVENTS_QUERY,
    {
      variables: loadUsingPartitionKeys
        ? {
            assetKey: {path: assetKey.path},
            before,
            partitionInLast: 120,
          }
        : {
            assetKey: {path: assetKey.path},
            before,
            limit: 100,
          },
    },
  );

  return React.useMemo(() => {
    const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;
    const materializations = asset?.assetMaterializations || [];
    const observations = asset?.assetObservations || [];

    const allPartitionKeys = asset?.definition?.partitionKeys;
    const loadedPartitionKeys =
      loadUsingPartitionKeys && allPartitionKeys
        ? allPartitionKeys.slice(allPartitionKeys.length - 120)
        : undefined;

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
}

const ASSET_EVENTS_QUERY = gql`
  query AssetEventsQuery(
    $assetKey: AssetKeyInput!
    $limit: Int
    $before: String
    $partitionInLast: Int
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
          partitionInLast: $partitionInLast
        ) {
          ...AssetObservationFragment
        }
        assetMaterializations(
          limit: $limit
          beforeTimestampMillis: $before
          partitionInLast: $partitionInLast
        ) {
          ...AssetMaterializationFragment
        }

        definition {
          id
          partitionKeys
        }
      }
    }
  }
  fragment AssetMaterializationFragment on MaterializationEvent {
    partition
    runOrError {
      ... on PipelineRun {
        id
        runId
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
  fragment AssetObservationFragment on ObservationEvent {
    partition
    runOrError {
      ... on PipelineRun {
        id
        runId
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
  ${ASSET_LINEAGE_FRAGMENT}
`;
