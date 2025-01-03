// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceBackfillsQueryVariables = Types.Exact<{
  status?: Types.InputMaybe<Types.BulkActionStatus>;
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;

export type InstanceBackfillsQuery = {
  __typename: 'Query';
  partitionBackfillsOrError:
    | {
        __typename: 'PartitionBackfills';
        results: Array<{
          __typename: 'PartitionBackfill';
          id: string;
          status: Types.BulkActionStatus;
          isValidSerialization: boolean;
          numPartitions: number | null;
          timestamp: number;
          partitionSetName: string | null;
          isAssetBackfill: boolean;
          hasCancelPermission: boolean;
          hasResumePermission: boolean;
          numCancelable: number;
          partitionNames: Array<string> | null;
          partitionSet: {
            __typename: 'PartitionSet';
            id: string;
            name: string;
            mode: string;
            pipelineName: string;
            repositoryOrigin: {
              __typename: 'RepositoryOrigin';
              id: string;
              repositoryName: string;
              repositoryLocationName: string;
            };
          } | null;
          error: {
            __typename: 'PythonError';
            message: string;
            stack: Array<string>;
            errorChain: Array<{
              __typename: 'ErrorChainLink';
              isExplicitLink: boolean;
              error: {__typename: 'PythonError'; message: string; stack: Array<string>};
            }>;
          } | null;
          assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        }>;
      }
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
};

export const InstanceBackfillsQueryVersion = 'b7b238631fe7f9d6c56285ae304ff6cf07446bed0da42e9d0d5d9339b01d9d6f';
