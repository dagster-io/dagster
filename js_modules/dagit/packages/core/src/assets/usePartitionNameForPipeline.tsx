import {gql, useQuery} from '@apollo/client';
import React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {RepoAddress} from '../workspace/types';

import {
  AssetJobPartitionSetsQuery,
  AssetJobPartitionSetsQueryVariables,
} from './types/AssetJobPartitionSetsQuery';

export function usePartitionNameForPipeline(repoAddress: RepoAddress, pipelineName: string) {
  const {data: partitionSetsData} = useQuery<
    AssetJobPartitionSetsQuery,
    AssetJobPartitionSetsQueryVariables
  >(ASSET_JOB_PARTITION_SETS_QUERY, {
    variables: {
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
      pipelineName,
    },
  });

  return React.useMemo(
    () => ({
      partitionSet:
        partitionSetsData?.partitionSetsOrError.__typename === 'PartitionSets'
          ? partitionSetsData.partitionSetsOrError.results[0]
          : undefined,
      partitionSetError:
        partitionSetsData?.partitionSetsOrError.__typename === 'PipelineNotFoundError' ||
        partitionSetsData?.partitionSetsOrError.__typename === 'PythonError'
          ? partitionSetsData.partitionSetsOrError
          : undefined,
    }),
    [partitionSetsData],
  );
}

const ASSET_JOB_PARTITION_SETS_QUERY = gql`
  query AssetJobPartitionSetsQuery(
    $pipelineName: String!
    $repositoryName: String!
    $repositoryLocationName: String!
  ) {
    partitionSetsOrError(
      pipelineName: $pipelineName
      repositorySelector: {
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      __typename
      ...PythonErrorFragment
      ... on PipelineNotFoundError {
        __typename
        message
      }
      ... on PartitionSets {
        __typename
        results {
          id
          name
          mode
          solidSelection
        }
      }
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
