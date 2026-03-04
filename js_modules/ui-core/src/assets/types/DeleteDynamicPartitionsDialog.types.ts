// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DeleteDynamicPartitionsMutationVariables = Types.Exact<{
  partitionKeys: Array<Types.Scalars['String']['input']> | Types.Scalars['String']['input'];
  partitionsDefName: Types.Scalars['String']['input'];
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
