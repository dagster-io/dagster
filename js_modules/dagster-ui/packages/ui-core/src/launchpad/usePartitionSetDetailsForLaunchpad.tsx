import * as React from 'react';

import {gql, useQuery} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {
  ConfigPartitionsAssetsQuery,
  ConfigPartitionsAssetsQueryVariables,
  ConfigPartitionsQuery,
  ConfigPartitionsQueryVariables,
} from './types/usePartitionSetDetailsForLaunchpad.types';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {PartitionDefinitionType, RepositorySelector} from '../graphql/types';

export function usePartitionSetDetailsForLaunchpad({
  pipelineName,
  partitionSetName,
  repositorySelector,
  assetSelection,
  skipConfigQuery,
}: {
  pipelineName: string;
  partitionSetName: string;
  repositorySelector: RepositorySelector;
  assetSelection?: IExecutionSession['assetSelection'];
  skipConfigQuery: boolean;
}) {
  const queryResultNoAssets = useQuery<ConfigPartitionsQuery, ConfigPartitionsQueryVariables>(
    CONFIG_PARTITIONS_QUERY,
    {
      skip: !!assetSelection || skipConfigQuery,
      variables: {repositorySelector, partitionSetName},
      fetchPolicy: 'network-only',
    },
  );

  const queryResultAssets = useQuery<
    ConfigPartitionsAssetsQuery,
    ConfigPartitionsAssetsQueryVariables
  >(CONFIG_PARTITIONS_ASSETS_QUERY, {
    skip: !assetSelection || skipConfigQuery,
    variables: {
      params: {...repositorySelector, pipelineName},
      assetKeys: assetSelection
        ? assetSelection.map((selection) => ({path: selection.assetKey.path}))
        : [],
    },
    fetchPolicy: 'network-only',
  });

  const queryResult = assetSelection ? queryResultAssets : queryResultNoAssets;
  const {data, refetch, loading} = queryResult;

  const doesAnyAssetHavePartitions = React.useMemo(
    () =>
      data && 'assetNodes' in data && data.assetNodes?.some((node) => !!node.partitionDefinition),
    [data],
  );

  const {isDynamicPartition, dynamicPartitionsDefinitionName} = React.useMemo(() => {
    const assetNodes = data && 'assetNodes' in data ? data?.assetNodes : undefined;
    const definition = assetNodes?.find((a) => !!a.partitionDefinition)?.partitionDefinition;
    if (
      !definition ||
      assetNodes?.some(
        (node) =>
          node?.partitionDefinition?.name && node?.partitionDefinition?.name !== definition?.name,
      )
    ) {
      return {isDynamicPartition: false, dynamicPartitionsDefinitionName: undefined};
    }
    return {
      isDynamicPartition: definition.type === PartitionDefinitionType.DYNAMIC,
      dynamicPartitionsDefinitionName: definition.name,
    };
  }, [data]);

  const retrieved: string[] = React.useMemo(() => {
    return partitionKeysFromData(data);
  }, [data]);

  const error = errorFromData(data);

  return {
    retrieved,
    error,
    loading,
    refetch,
    partitionSetName,
    isDynamicPartition,
    dynamicPartitionsDefinitionName,
    doesAnyAssetHavePartitions,
  };
}

export type PartitionSetDetails = ReturnType<typeof usePartitionSetDetailsForLaunchpad>;

const CONFIG_PARTITIONS_QUERY = gql`
  query ConfigPartitionsQuery(
    $repositorySelector: RepositorySelector!
    $partitionSetName: String!
  ) {
    partitionSetOrError(
      repositorySelector: $repositorySelector
      partitionSetName: $partitionSetName
    ) {
      ... on PartitionSet {
        id
        partitionsOrError {
          ... on Partitions {
            results {
              ...ConfigPartitionResult
            }
          }
          ...PythonErrorFragment
        }
      }
    }
  }

  fragment ConfigPartitionResult on Partition {
    name
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const CONFIG_PARTITIONS_ASSETS_QUERY = gql`
  query ConfigPartitionsAssetsQuery($params: PipelineSelector!, $assetKeys: [AssetKeyInput!]) {
    pipelineOrError(params: $params) {
      ...PythonErrorFragment
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on Pipeline {
        id
        partitionKeysOrError(selectedAssetKeys: $assetKeys) {
          ... on PartitionKeys {
            partitionKeys
          }
        }
      }
    }
    assetNodes(assetKeys: $assetKeys) {
      id
      partitionDefinition {
        name
        type
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

function partitionKeysFromData(
  data: ConfigPartitionsAssetsQuery | ConfigPartitionsQuery | undefined,
) {
  if (!data) {
    return [];
  }

  if (
    'partitionSetOrError' in data &&
    data.partitionSetOrError.__typename === 'PartitionSet' &&
    data.partitionSetOrError.partitionsOrError.__typename === 'Partitions'
  ) {
    return data.partitionSetOrError.partitionsOrError.results.map((a) => a.name);
  }
  if ('pipelineOrError' in data && data.pipelineOrError.__typename === 'Pipeline') {
    return data.pipelineOrError.partitionKeysOrError.partitionKeys;
  }
  return [];
}

function errorFromData(data: ConfigPartitionsAssetsQuery | ConfigPartitionsQuery | undefined) {
  if (!data) {
    return null;
  }
  if (
    'partitionSetOrError' in data &&
    data.partitionSetOrError.__typename === 'PartitionSet' &&
    data.partitionSetOrError.partitionsOrError.__typename !== 'Partitions'
  ) {
    return data.partitionSetOrError.partitionsOrError;
  }
  if (
    'pipelineOrError' in data &&
    data.pipelineOrError &&
    data.pipelineOrError.__typename !== 'Pipeline'
  ) {
    return data.pipelineOrError;
  }
  return null;
}
