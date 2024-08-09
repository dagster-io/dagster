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
