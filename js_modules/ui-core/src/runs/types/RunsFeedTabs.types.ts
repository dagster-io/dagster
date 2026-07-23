/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

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

export type RunFeedTabsCountQueryVariables = Exact<{
  queuedFilter: Types.RunsFilter;
  inProgressFilter: Types.RunsFilter;
  view: Types.RunsFeedView;
}>;

export type RunFeedTabsCountQuery = {
  __typename: 'Query';
  queuedCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
  inProgressCount: {__typename: 'PythonError'} | {__typename: 'RunsFeedCount'; count: number};
};

export const RunFeedTabsCountQueryVersion = '5bf6c4d00cebf6817ce69cc4fc6d25c99b98f7a9031934b61187f95020880b4a';
