import {useMemo, useState} from 'react';

import {gql, useApolloClient} from '../../apollo-client';
import {AssetPartitionStatus} from '../AssetPartitionStatus';
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
  statusForPartition: (dimensionKey: string) => AssetPartitionStatus[];
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

  if (!assetNode?.assetChecksOrError || assetNode.assetChecksOrError.__typename !== 'AssetChecks') {
    return null;
  }

  const check = assetNode.assetChecksOrError.checks.find((c) => c.name === checkName);
  if (!check) {
    return null;
  }

  const dimensions = (check.partitionKeysByDimension || []).map((dim) => ({
    name: dim.name,
    partitionKeys: dim.partitionKeys,
  }));

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const dim = dimensions[0]!;
  const partitions = dimensions.length > 0 ? dim.partitionKeys : [];

  const partitionStatusMap = new Map<string, AssetPartitionStatus[]>();
  const executions = data.assetCheckExecutions || [];

  for (const partition of partitions) {
    partitionStatusMap.set(partition, [AssetPartitionStatus.MISSING]);
  }

  for (const execution of executions) {
    const partition = execution.evaluation?.partition;
    if (partition && partitions.includes(partition)) {
      const status = getStatusFromExecution(execution);
      partitionStatusMap.set(partition, [status]);
    }
  }

  const statusForPartition = (dimensionKey: string): AssetPartitionStatus[] => {
    return partitionStatusMap.get(dimensionKey) || [AssetPartitionStatus.MISSING];
  };

  return {
    assetKey,
    checkName,
    dimensions,
    partitions,
    statusForPartition,
  };
}

function getStatusFromExecution(execution: any): AssetPartitionStatus {
  if (!execution.evaluation) {
    return AssetPartitionStatus.MISSING;
  }

  switch (execution.status) {
    case 'SUCCEEDED':
      return execution.evaluation.success
        ? AssetPartitionStatus.MATERIALIZED
        : AssetPartitionStatus.FAILED;
    case 'IN_PROGRESS':
      return AssetPartitionStatus.MATERIALIZING;
    case 'FAILED':
    case 'EXECUTION_FAILED':
      return AssetPartitionStatus.FAILED;
    case 'SKIPPED':
    default:
      return AssetPartitionStatus.MISSING;
  }
}

export const ASSET_CHECK_PARTITION_HEALTH_QUERY = gql`
  query AssetCheckPartitionHealthQuery($assetKey: AssetKeyInput!, $checkName: String!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        assetChecksOrError {
          ... on AssetChecks {
            checks {
              name
              partitionKeysByDimension {
                name
                partitionKeys
              }
            }
          }
        }
      }
    }
    assetCheckExecutions(assetKey: $assetKey, checkName: $checkName, limit: 1000) {
      id
      status
      evaluation {
        success
        partition
      }
    }
  }
`;
