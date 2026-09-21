/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type BulkActionStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'COMPLETED'
  | 'COMPLETED_FAILED'
  | 'COMPLETED_SUCCESS'
  | 'FAILED'
  | 'FAILING'
  | 'REQUESTED';

export type ExecutionTag = {
  key: string;
  value: string;
};

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type RunsFeedView = 'BACKFILLS' | 'ROOTS' | 'RUNS';

export type RunsFilter = {
  createdAfter?: number | null | undefined;
  createdBefore?: number | null | undefined;
  mode?: string | null | undefined;
  pipelineName?: string | null | undefined;
  runIds?: Array<string | null | undefined> | null | undefined;
  snapshotId?: string | null | undefined;
  statuses?: Array<RunStatus> | null | undefined;
  tags?: Array<ExecutionTag> | null | undefined;
  updatedAfter?: number | null | undefined;
  updatedBefore?: number | null | undefined;
};

export type RunsFeedRootQueryVariables = Exact<{
  limit: number;
  cursor?: string | null | undefined;
  filter?: Types.RunsFilter | null | undefined;
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
              numPartitions: number | null;
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
            }
          | {
              __typename: 'Run';
              id: string;
              assetSelectionCount: number;
              assetCheckSelectionCount: number;
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
              assetSelectionPreview: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
              assetCheckSelectionPreview: Array<{
                __typename: 'AssetCheckhandle';
                name: string;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              }> | null;
              tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
            }
        >;
      };
};

export const RunsFeedRootQueryVersion = 'f38be3e2c65b5e52f0abc3fb7bceea28caf2bdb5bebdd4d8977c1f0d91cae61e';
