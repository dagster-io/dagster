/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RepositorySelector = {
  repositoryLocationName: string;
  repositoryName: string;
};

export type AddDynamicPartitionMutationVariables = Exact<{
  partitionsDefName: string;
  partitionKey: string;
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
