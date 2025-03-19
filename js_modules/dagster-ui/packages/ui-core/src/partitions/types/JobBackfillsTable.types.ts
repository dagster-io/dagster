// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type JobBackfillsQueryVariables = Types.Exact<{
  partitionSetName: Types.Scalars['String']['input'];
  repositorySelector: Types.RepositorySelector;
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
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
          numPartitions: number | null;
          timestamp: number;
          partitionSetName: string | null;
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

export const JobBackfillsQueryVersion = 'a9bbbaba978437e454ea9e874d1198be990c01860540ef0cfc7bc601b357a7d6';
