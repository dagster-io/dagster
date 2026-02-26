import {MockedResponse} from '@apollo/client/testing';

import {CREATE_PARTITION_MUTATION} from '../CreatePartitionDialog';
import {
  AddDynamicPartitionMutation,
  AddDynamicPartitionMutationVariables,
} from '../types/CreatePartitionDialog.types';

export function buildCreatePartitionFixture({
  partitionsDefName,
  partitionKey,
}: {
  partitionsDefName: string;
  partitionKey: string;
}): MockedResponse<AddDynamicPartitionMutation> {
  return {
    request: {
      query: CREATE_PARTITION_MUTATION,
      variables: {
        partitionsDefName,
        partitionKey,
        repositorySelector: {
          repositoryLocationName: 'testing',
          repositoryName: 'testing',
        },
      },
    },
    result: jest.fn(() => ({
      data: {
        __typename: 'Mutation',
        addDynamicPartition: {
          __typename: 'AddDynamicPartitionSuccess',
          partitionsDefName: partitionKey,
          partitionKey,
        },
      },
    })),
  };
}

export function buildCreatePartitionMutation({
  variables,
  data,
}: {
  variables: AddDynamicPartitionMutationVariables;
  data: AddDynamicPartitionMutation['addDynamicPartition'];
}): MockedResponse<AddDynamicPartitionMutation> {
  return {
    request: {
      query: CREATE_PARTITION_MUTATION,
      variables,
    },
    result: jest.fn(() => ({
      data: {
        __typename: 'Mutation',
        addDynamicPartition: data,
      },
    })),
  };
}
