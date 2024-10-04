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
          partitionNames: Array<string> | null;
          hasCancelPermission: boolean;
          hasResumePermission: boolean;
          numCancelable: number;
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

export const InstanceBackfillsQueryVersion = 'e9baee9c4eabc561ffe1ffcb06430969883c1d1cfb469438f98d821b90d3d06a';
