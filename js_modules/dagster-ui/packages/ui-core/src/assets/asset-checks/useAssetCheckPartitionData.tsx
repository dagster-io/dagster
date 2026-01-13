import {useMemo, useState} from 'react';

import {AssetCheckPartitionStatus} from './AssetCheckPartitionStatus';
import {gql, useApolloClient} from '../../apollo-client';
import {AssetCheckPartitionRangeStatus} from '../../graphql/types';
import {usePartitionDataSubscriber} from '../PartitionSubscribers';
import {AssetKey} from '../types';
import {
  AssetCheckPartitionHealthQuery,
  AssetCheckPartitionHealthQueryVariables,
} from './types/useAssetCheckPartitionData.types';

export interface AssetCheckPartitionData {
  assetKey: AssetKey;
  checkName: string;
  dimensions: AssetCheckPartitionDimension[];
  partitions: string[];
  statusForPartition: (dimensionKey: string) => AssetCheckPartitionStatus;
}

export interface AssetCheckPartitionDimension {
  name: string;
  partitionKeys: string[];
}

export function useAssetCheckPartitionData(assetKey: AssetKey | null, checkName: string | null) {
  const [partitionsLastUpdated, setPartitionsLastUpdatedAt] = useState<string>('');
  usePartitionDataSubscriber(() => {
    setPartitionsLastUpdatedAt(Date.now().toString());
  });

  const cacheKey = `${JSON.stringify(assetKey)}-${checkName}-${partitionsLastUpdated}`;
  const [result, setResult] = useState<(AssetCheckPartitionData & {fetchedAt: string}) | null>(
    null,
  );
  const client = useApolloClient();

  const [loading, setLoading] = useState(true);

  // Fetch partition data for the asset check
  useMemo(() => {
    if (!assetKey || !checkName) {
      setLoading(false);
      setResult(null);
      return;
    }

    // Check if we already have this data cached
    if (
      result &&
      result.assetKey === assetKey &&
      result.checkName === checkName &&
      result.fetchedAt === cacheKey
    ) {
      setLoading(false);
      return;
    }

    const run = async () => {
      try {
        const {data} = await client.query<
          AssetCheckPartitionHealthQuery,
          AssetCheckPartitionHealthQueryVariables
        >({
          query: ASSET_CHECK_PARTITION_HEALTH_QUERY,
          fetchPolicy: 'network-only',
          variables: {
            assetKey: {path: assetKey.path},
            checkName,
          },
        });

        const loaded = buildAssetCheckPartitionData(data, assetKey, checkName);
        setResult(loaded ? {...loaded, fetchedAt: cacheKey} : null);
      } catch (error) {
        console.error('Failed to fetch asset check partition data:', error);
        setResult(null);
      }
      setLoading(false);
    };
    run();
  }, [client, assetKey, checkName, cacheKey, result]);

  return {data: result, loading};
}

function rangeStatusToPartitionStatus(
  rangeStatus: AssetCheckPartitionRangeStatus,
): AssetCheckPartitionStatus {
  switch (rangeStatus) {
    case 'SUCCEEDED':
      return AssetCheckPartitionStatus.SUCCEEDED;
    case 'FAILED':
      return AssetCheckPartitionStatus.FAILED;
    case 'IN_PROGRESS':
      return AssetCheckPartitionStatus.IN_PROGRESS;
    case 'SKIPPED':
      return AssetCheckPartitionStatus.SKIPPED;
    case 'EXECUTION_FAILED':
      return AssetCheckPartitionStatus.EXECUTION_FAILED;
    default:
      return AssetCheckPartitionStatus.MISSING;
  }
}

function buildAssetCheckPartitionData(
  data: AssetCheckPartitionHealthQuery,
  assetKey: AssetKey,
  checkName: string,
): AssetCheckPartitionData | null {
  const assetNode = data.assetNodeOrError.__typename === 'AssetNode' ? data.assetNodeOrError : null;

  if (!assetNode?.assetCheckOrError || assetNode.assetCheckOrError.__typename !== 'AssetCheck') {
    return null;
  }

  const check = assetNode.assetCheckOrError;

  const dimensions = (check.partitionKeysByDimension || []).map((dim) => ({
    name: dim.name,
    partitionKeys: dim.partitionKeys,
  }));

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const dim = dimensions[0]!;
  const partitions = dimensions.length > 0 ? dim.partitionKeys : [];

  const partitionStatusMap = new Map<string, AssetCheckPartitionStatus>();
  const partitionStatuses = check.partitionStatuses;

  // Initialize all partitions as missing
  for (const partition of partitions) {
    partitionStatusMap.set(partition, AssetCheckPartitionStatus.MISSING);
  }

  // Update with actual statuses from GraphQL
  // Missing status is calculated as the complement of all known statuses
  if (partitionStatuses) {
    // Handle union type - check __typename
    if (partitionStatuses.__typename === 'AssetCheckDefaultPartitionStatuses') {
      // Process each status type for default partitions
      partitionStatuses.succeededPartitions?.forEach((partition) => {
        partitionStatusMap.set(partition, AssetCheckPartitionStatus.SUCCEEDED);
      });

      partitionStatuses.failedPartitions?.forEach((partition) => {
        partitionStatusMap.set(partition, AssetCheckPartitionStatus.FAILED);
      });

      partitionStatuses.inProgressPartitions?.forEach((partition) => {
        partitionStatusMap.set(partition, AssetCheckPartitionStatus.IN_PROGRESS);
      });

      partitionStatuses.skippedPartitions?.forEach((partition) => {
        partitionStatusMap.set(partition, AssetCheckPartitionStatus.SKIPPED);
      });

      partitionStatuses.executionFailedPartitions?.forEach((partition) => {
        partitionStatusMap.set(partition, AssetCheckPartitionStatus.EXECUTION_FAILED);
      });
    } else if (partitionStatuses.__typename === 'AssetCheckTimePartitionStatuses') {
      // For time partitions, extract partition keys from ranges
      partitionStatuses.ranges?.forEach((range) => {
        // Expand range to individual partition keys
        const status = rangeStatusToPartitionStatus(range.status);
        const startIdx = partitions.indexOf(range.startKey);
        const endIdx = partitions.indexOf(range.endKey);

        if (startIdx !== -1 && endIdx !== -1) {
          // Set status for all partitions in the range [startIdx, endIdx]
          for (let i = startIdx; i <= endIdx; i++) {
            const partitionKey = partitions[i];
            if (partitionKey) {
              partitionStatusMap.set(partitionKey, status);
            }
          }
        }
      });
    } else if (partitionStatuses.__typename === 'AssetCheckMultiPartitionStatuses') {
      // Multi-partition handling would require more complex logic
      // For now, we'll leave this as MISSING (default)
      console.warn('Multi-partition status display not yet fully implemented');
    }
  }

  const statusForPartition = (dimensionKey: string): AssetCheckPartitionStatus => {
    return partitionStatusMap.get(dimensionKey) || AssetCheckPartitionStatus.MISSING;
  };

  return {
    assetKey,
    checkName,
    dimensions,
    partitions,
    statusForPartition,
  };
}

export const ASSET_CHECK_PARTITION_HEALTH_QUERY = gql`
  query AssetCheckPartitionHealthQuery($assetKey: AssetKeyInput!, $checkName: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        assetCheckOrError(checkName: $checkName) {
          ... on AssetCheck {
            name
            partitionKeysByDimension {
              name
              partitionKeys
            }
            partitionStatuses {
              ... on AssetCheckDefaultPartitionStatuses {
                succeededPartitions
                failedPartitions
                inProgressPartitions
                skippedPartitions
                executionFailedPartitions
              }
              ... on AssetCheckTimePartitionStatuses {
                ranges {
                  startTime
                  endTime
                  startKey
                  endKey
                  status
                }
              }
              ... on AssetCheckMultiPartitionStatuses {
                primaryDimensionName
                ranges {
                  primaryDimStartKey
                  primaryDimEndKey
                  primaryDimStartTime
                  primaryDimEndTime
                  secondaryDim {
                    ... on AssetCheckTimePartitionStatuses {
                      ranges {
                        startTime
                        endTime
                        startKey
                        endKey
                        status
                      }
                    }
                    ... on AssetCheckDefaultPartitionStatuses {
                      succeededPartitions
                      failedPartitions
                      inProgressPartitions
                      skippedPartitions
                      executionFailedPartitions
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
`;
