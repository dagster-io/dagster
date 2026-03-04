import {useEffect, useState} from 'react';

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
  statusForPartitionKeys: (dimensionKeys: string[]) => AssetCheckPartitionStatus;
  statusForDim0Aggregate: (dim0Key: string) => AssetCheckPartitionStatus;
  statusForDimAggregate: (dimIdx: number, key: string) => AssetCheckPartitionStatus;
  statusesForDimAggregate: (dimIdx: number, key: string) => AssetCheckPartitionStatus[];
}

export interface AssetCheckPartitionDimension {
  name: string;
  type: string;
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
  useEffect(() => {
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

// Priority order for "worst" status (lower index = worse)
const STATUS_SEVERITY: AssetCheckPartitionStatus[] = [
  AssetCheckPartitionStatus.FAILED,
  AssetCheckPartitionStatus.EXECUTION_FAILED,
  AssetCheckPartitionStatus.IN_PROGRESS,
  AssetCheckPartitionStatus.SKIPPED,
  AssetCheckPartitionStatus.MISSING,
  AssetCheckPartitionStatus.SUCCEEDED,
];

function worstStatus(statuses: AssetCheckPartitionStatus[]): AssetCheckPartitionStatus {
  const values = new Set(statuses.map((status) => STATUS_SEVERITY.indexOf(status)));
  const min = Math.min(...Array.from(values));
  return STATUS_SEVERITY[min] ?? AssetCheckPartitionStatus.SUCCEEDED;
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
    type: dim.type,
    partitionKeys: dim.partitionKeys,
  }));

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const dim = dimensions[0]!;
  const partitions = dimensions.length > 0 ? dim.partitionKeys : [];

  const partitionStatusMap = new Map<string, AssetCheckPartitionStatus>();
  // 2D status map: dim0Key -> dim1Key -> status
  const multiPartitionStatusMap = new Map<string, Map<string, AssetCheckPartitionStatus>>();
  const isMultiPartition = dimensions.length > 1;

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
      // Determine dimension ordering - primaryDimensionName may not match dimensions[0]
      const primaryMatchesDim0 = partitionStatuses.primaryDimensionName === dimensions[0]?.name;
      const dim0Keys = dimensions[0]?.partitionKeys ?? [];
      const dim1Keys = dimensions[1]?.partitionKeys ?? [];

      // Resolve which keys correspond to primary vs secondary
      const primaryKeys = primaryMatchesDim0 ? dim0Keys : dim1Keys;
      const secondaryKeys = primaryMatchesDim0 ? dim1Keys : dim0Keys;

      for (const range of partitionStatuses.ranges) {
        // Expand primary dimension range to individual keys
        const startIdx = primaryKeys.indexOf(range.primaryDimStartKey);
        const endIdx = primaryKeys.indexOf(range.primaryDimEndKey);
        if (startIdx === -1 || endIdx === -1) {
          continue;
        }

        for (let pi = startIdx; pi <= endIdx; pi++) {
          const primaryKey = primaryKeys[pi];
          if (!primaryKey) {
            continue;
          }

          // Build secondary dim status map for this primary key
          const secondaryStatuses = new Map<string, AssetCheckPartitionStatus>();
          const secondaryDim = range.secondaryDim;

          if (secondaryDim.__typename === 'AssetCheckDefaultPartitionStatuses') {
            secondaryDim.succeededPartitions?.forEach((k) => {
              secondaryStatuses.set(k, AssetCheckPartitionStatus.SUCCEEDED);
            });
            secondaryDim.failedPartitions?.forEach((k) => {
              secondaryStatuses.set(k, AssetCheckPartitionStatus.FAILED);
            });
            secondaryDim.inProgressPartitions?.forEach((k) => {
              secondaryStatuses.set(k, AssetCheckPartitionStatus.IN_PROGRESS);
            });
            secondaryDim.skippedPartitions?.forEach((k) => {
              secondaryStatuses.set(k, AssetCheckPartitionStatus.SKIPPED);
            });
            secondaryDim.executionFailedPartitions?.forEach((k) => {
              secondaryStatuses.set(k, AssetCheckPartitionStatus.EXECUTION_FAILED);
            });
          } else if (secondaryDim.__typename === 'AssetCheckTimePartitionStatuses') {
            secondaryDim.ranges?.forEach((r) => {
              const status = rangeStatusToPartitionStatus(r.status);
              const sStart = secondaryKeys.indexOf(r.startKey);
              const sEnd = secondaryKeys.indexOf(r.endKey);
              if (sStart !== -1 && sEnd !== -1) {
                for (let si = sStart; si <= sEnd; si++) {
                  const secKey = secondaryKeys[si];
                  if (secKey) {
                    secondaryStatuses.set(secKey, status);
                  }
                }
              }
            });
          }

          // Store in the 2D map with dim0/dim1 ordering (regardless of primary/secondary)
          if (primaryMatchesDim0) {
            let dim1Map = multiPartitionStatusMap.get(primaryKey);
            if (!dim1Map) {
              dim1Map = new Map();
              multiPartitionStatusMap.set(primaryKey, dim1Map);
            }
            for (const [secKey, status] of secondaryStatuses) {
              dim1Map.set(secKey, status);
            }
          } else {
            // Primary is dim1, secondary is dim0 - invert the nesting
            for (const [secKey, status] of secondaryStatuses) {
              let dim1Map = multiPartitionStatusMap.get(secKey);
              if (!dim1Map) {
                dim1Map = new Map();
                multiPartitionStatusMap.set(secKey, dim1Map);
              }
              dim1Map.set(primaryKey, status);
            }
          }
        }
      }
    }
  }

  const statusForPartition = (dimensionKey: string): AssetCheckPartitionStatus => {
    return partitionStatusMap.get(dimensionKey) || AssetCheckPartitionStatus.MISSING;
  };

  const statusForPartitionKeys = (dimensionKeys: string[]): AssetCheckPartitionStatus => {
    if (!isMultiPartition || dimensionKeys.length === 1) {
      return partitionStatusMap.get(dimensionKeys[0] ?? '') ?? AssetCheckPartitionStatus.MISSING;
    }
    const [k0, k1] = dimensionKeys;
    return (
      multiPartitionStatusMap.get(k0 ?? '')?.get(k1 ?? '') ?? AssetCheckPartitionStatus.MISSING
    );
  };

  const statusForDim0Aggregate = (dim0Key: string): AssetCheckPartitionStatus => {
    if (!isMultiPartition) {
      return partitionStatusMap.get(dim0Key) ?? AssetCheckPartitionStatus.MISSING;
    }
    const dim1Map = multiPartitionStatusMap.get(dim0Key);
    if (!dim1Map || dim1Map.size === 0) {
      return AssetCheckPartitionStatus.MISSING;
    }
    return worstStatus(Array.from(dim1Map.values()));
  };

  const statusForDimAggregate = (dimIdx: number, key: string): AssetCheckPartitionStatus => {
    if (!isMultiPartition) {
      return partitionStatusMap.get(key) ?? AssetCheckPartitionStatus.MISSING;
    }
    if (dimIdx === 0) {
      return statusForDim0Aggregate(key);
    }
    // For dim1, aggregate across all dim0 keys
    const dim0Keys = dimensions[0]?.partitionKeys ?? [];
    const statuses: AssetCheckPartitionStatus[] = [];
    for (const d0 of dim0Keys) {
      statuses.push(multiPartitionStatusMap.get(d0)?.get(key) ?? AssetCheckPartitionStatus.MISSING);
    }
    return statuses.length === 0 ? AssetCheckPartitionStatus.MISSING : worstStatus(statuses);
  };

  // Returns all distinct statuses for a dimension key (for multi-status display in status bar)
  const statusesForDimAggregate = (dimIdx: number, key: string): AssetCheckPartitionStatus[] => {
    if (!isMultiPartition) {
      return [partitionStatusMap.get(key) ?? AssetCheckPartitionStatus.MISSING];
    }
    const otherDimIdx = dimIdx === 0 ? 1 : 0;
    const otherKeys = dimensions[otherDimIdx]?.partitionKeys ?? [];
    const statusSet = new Set<AssetCheckPartitionStatus>();
    for (const otherKey of otherKeys) {
      const cellKeys = dimIdx === 0 ? [key, otherKey] : [otherKey, key];
      statusSet.add(statusForPartitionKeys(cellKeys));
    }
    if (statusSet.size === 0) {
      return [AssetCheckPartitionStatus.MISSING];
    }
    // Sort by severity for consistent ordering
    return STATUS_SEVERITY.filter((s) => statusSet.has(s));
  };

  return {
    assetKey,
    checkName,
    dimensions,
    partitions,
    statusForPartition,
    statusForPartitionKeys,
    statusForDim0Aggregate,
    statusForDimAggregate,
    statusesForDimAggregate,
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
              type
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
