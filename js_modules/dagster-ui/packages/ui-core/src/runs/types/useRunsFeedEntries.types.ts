// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunsFeedRootQueryVariables = Types.Exact<{
  limit: Types.Scalars['Int']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  filter?: Types.InputMaybe<Types.RunsFilter>;
  view: Types.RunsFeedView;
}>;

export type RunsFeedRootQuery = {
  __typename: 'Query';
  runsFeedOrError:
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
    | {
        __typename: 'RunsFeedConnection';
        cursor: string;
        hasMore: boolean;
        results: Array<
          | {
              __typename: 'PartitionBackfill';
              id: string;
              partitionSetName: string | null;
              hasCancelPermission: boolean;
              hasResumePermission: boolean;
              isAssetBackfill: boolean;
              numCancelable: number;
              runStatus: Types.RunStatus;
              creationTime: number;
              startTime: number | null;
              endTime: number | null;
              jobName: string | null;
              partitionNames: Array<string> | null;
              backfillStatus: Types.BulkActionStatus;
              partitionSet: {
                __typename: 'PartitionSet';
                id: string;
                mode: string;
                name: string;
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
              assetCheckSelection: Array<{
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }> | null;
            }
          | {
              __typename: 'Run';
              id: string;
              runStatus: Types.RunStatus;
              creationTime: number;
              startTime: number | null;
              endTime: number | null;
              jobName: string;
              hasReExecutePermission: boolean;
              hasTerminatePermission: boolean;
              hasDeletePermission: boolean;
              canTerminate: boolean;
              mode: string;
              status: Types.RunStatus;
              pipelineName: string;
              pipelineSnapshotId: string | null;
              hasRunMetricsEnabled: boolean;
              repositoryOrigin: {
                __typename: 'RepositoryOrigin';
                id: string;
                repositoryName: string;
                repositoryLocationName: string;
              } | null;
              tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
              assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
              assetCheckSelection: Array<{
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }> | null;
            }
        >;
      };
};

export const RunsFeedRootQueryVersion = 'ea4f2297073d32b2be0b82c42ea13a8f8cdd7b163dda0153b5633bfc7de5a7fd';
