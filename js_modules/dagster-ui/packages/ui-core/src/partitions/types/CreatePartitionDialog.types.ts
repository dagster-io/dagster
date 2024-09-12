// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AddDynamicPartitionMutationVariables = Types.Exact<{
  partitionsDefName: Types.Scalars['String']['input'];
  partitionKey: Types.Scalars['String']['input'];
  repositorySelector: Types.RepositorySelector;
}>;

export type AddDynamicPartitionMutation = {
  __typename: 'Mutation';
  addDynamicPartition:
    | {__typename: 'AddDynamicPartitionSuccess'; partitionsDefName: string; partitionKey: string}
    | {__typename: 'DuplicateDynamicPartitionError'}
    | {__typename: 'PythonError'; message: string; stack: Array<string>}
    | {__typename: 'UnauthorizedError'; message: string};
};

export const AddDynamicPartitionMutationVersion = '09fbfa963ad43c7fecfc8e4f780e1ca98ffcea9f0b04e916c78061667cb250eb';
