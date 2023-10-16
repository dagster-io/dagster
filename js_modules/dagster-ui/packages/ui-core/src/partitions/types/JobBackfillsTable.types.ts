// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type JobBackfillsQueryVariables = Types.Exact<{
  partitionSetName: Types.Scalars['String'];
  repositorySelector: Types.RepositorySelector;
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']>;
}>;

export type JobBackfillsQuery = {
  __typename: 'Query';
  partitionSetOrError:
    | {
        __typename: 'PartitionSet';
        id: string;
        pipelineName: string;
        backfills: Array<{
          __typename: 'PartitionBackfill';
          id: string;
          status: Types.BulkActionStatus;
          isAssetBackfill: boolean;
          isValidSerialization: boolean;
          partitionNames: Array<string> | null;
          numPartitions: number | null;
          timestamp: number;
          partitionSetName: string | null;
          blockedReason: string | null;
          hasCancelPermission: boolean;
          hasResumePermission: boolean;
          numCancelable: number;
          partitionSet: {
            __typename: 'PartitionSet';
            id: string;
            name: string;
            pipelineName: string;
            mode: string;
            repositoryOrigin: {
              __typename: 'RepositoryOrigin';
              repositoryName: string;
              repositoryLocationName: string;
              id: string;
            };
          } | null;
          assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
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
        }>;
      }
    | {__typename: 'PartitionSetNotFoundError'}
    | {__typename: 'PythonError'};
};
