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
