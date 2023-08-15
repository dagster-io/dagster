import {gql, useQuery} from '@apollo/client';
import React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {RepoAddress} from '../workspace/types';

import {
  AssetJobPartitionSetsQuery,
  AssetJobPartitionSetsQueryVariables,
} from './types/usePartitionNameForPipeline.types';

export function usePartitionNameForPipeline(repoAddress: RepoAddress, pipelineName: string) {
  const {data: partitionSetsData} = useQuery<
    AssetJobPartitionSetsQuery,
    AssetJobPartitionSetsQueryVariables
  >(ASSET_JOB_PARTITION_SETS_QUERY, {
    skip: !pipelineName,
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

export const ASSET_JOB_PARTITION_SETS_QUERY = gql`
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
      ... on PipelineNotFoundError {
        message
      }
      ... on PartitionSets {
        results {
          id
          name
          mode
          solidSelection
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
