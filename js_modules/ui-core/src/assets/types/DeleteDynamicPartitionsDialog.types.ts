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

export type DeleteDynamicPartitionsMutationVariables = Exact<{
  partitionKeys: Array<string> | string;
  partitionsDefName: string;
  repositorySelector: Types.RepositorySelector;
}>;

export type DeleteDynamicPartitionsMutation = {
  __typename: 'Mutation';
  deleteDynamicPartitions:
    | {__typename: 'DeleteDynamicPartitionsSuccess'}
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export const DeleteDynamicPartitionsMutationVersion = 'dc34ce729a12d80db6cabbb4ed9093ee29b9c4e2c6843074b13b67b454b61471';

export const DeleteVersion = '3c61c79b99122910e754a8863e80dc5ed479a0c23cc1a9d9878d91e603fc0dfe';
