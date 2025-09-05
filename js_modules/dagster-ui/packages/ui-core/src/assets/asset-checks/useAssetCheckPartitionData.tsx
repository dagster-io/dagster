import {useMemo, useState} from 'react';

import {AssetCheckPartitionStatus} from './AssetCheckPartitionStatus';
import {gql, useApolloClient} from '../../apollo-client';
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
  if (partitionStatuses) {
    // Process each status type
    partitionStatuses.missing?.forEach((partition) => {
      partitionStatusMap.set(partition, AssetCheckPartitionStatus.MISSING);
    });

    partitionStatuses.succeeded?.forEach((partition) => {
      partitionStatusMap.set(partition, AssetCheckPartitionStatus.SUCCEEDED);
    });

    partitionStatuses.failed?.forEach((partition) => {
      partitionStatusMap.set(partition, AssetCheckPartitionStatus.FAILED);
    });

    partitionStatuses.inProgress?.forEach((partition) => {
      partitionStatusMap.set(partition, AssetCheckPartitionStatus.IN_PROGRESS);
    });

    partitionStatuses.skipped?.forEach((partition) => {
      partitionStatusMap.set(partition, AssetCheckPartitionStatus.SKIPPED);
    });

    partitionStatuses.executionFailed?.forEach((partition) => {
      partitionStatusMap.set(partition, AssetCheckPartitionStatus.EXECUTION_FAILED);
    });
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
              missing
              succeeded
              failed
              inProgress
              skipped
              executionFailed
            }
          }
        }
      }
    }
  }
`;
