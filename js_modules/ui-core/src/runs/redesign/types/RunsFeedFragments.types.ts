/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BulkActionStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'COMPLETED'
  | 'COMPLETED_FAILED'
  | 'COMPLETED_SUCCESS'
  | 'FAILED'
  | 'FAILING'
  | 'REQUESTED';

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

export type RunSummaryFragment = {
  __typename: 'Run';
  id: string;
  runId: string;
  runStatus: Types.RunStatus;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  jobName: string;
  mode: string;
  pipelineSnapshotId: string | null;
  parentRunId: string | null;
  rootRunId: string | null;
  assetSelectionCount: number;
  assetCheckSelectionCount: number;
  hasReExecutePermission: boolean;
  hasTerminatePermission: boolean;
  hasDeletePermission: boolean;
  canTerminate: boolean;
  hasRunMetricsEnabled: boolean;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    id: string;
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  assetSelectionPreview: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  assetCheckSelectionPreview: Array<{
    __typename: 'AssetCheckhandle';
    name: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }> | null;
};

export type BackfillSummaryFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  runStatus: Types.RunStatus;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  partitionSetName: string | null;
  isAssetBackfill: boolean;
  title: string | null;
  user: string | null;
  hasCancelPermission: boolean;
  hasResumePermission: boolean;
  backfillStatus: Types.BulkActionStatus;
  backfillJobName: string | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export type RunsFeedEntryFragment_PartitionBackfill = {
  __typename: 'PartitionBackfill';
  id: string;
  runStatus: Types.RunStatus;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  partitionSetName: string | null;
  isAssetBackfill: boolean;
  title: string | null;
  user: string | null;
  hasCancelPermission: boolean;
  hasResumePermission: boolean;
  backfillStatus: Types.BulkActionStatus;
  backfillJobName: string | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export type RunsFeedEntryFragment_Run = {
  __typename: 'Run';
  id: string;
  runId: string;
  runStatus: Types.RunStatus;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  jobName: string;
  mode: string;
  pipelineSnapshotId: string | null;
  parentRunId: string | null;
  rootRunId: string | null;
  assetSelectionCount: number;
  assetCheckSelectionCount: number;
  hasReExecutePermission: boolean;
  hasTerminatePermission: boolean;
  hasDeletePermission: boolean;
  canTerminate: boolean;
  hasRunMetricsEnabled: boolean;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    id: string;
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  assetSelectionPreview: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  assetCheckSelectionPreview: Array<{
    __typename: 'AssetCheckhandle';
    name: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }> | null;
};

export type RunsFeedEntryFragment =
  | RunsFeedEntryFragment_PartitionBackfill
  | RunsFeedEntryFragment_Run;

export type RunSelectionDetailsFragment = {
  __typename: 'Run';
  id: string;
  runId: string;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  assetCheckSelection: Array<{
    __typename: 'AssetCheckhandle';
    name: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }> | null;
  executionPlan: {
    __typename: 'ExecutionPlan';
    assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    steps: Array<{__typename: 'ExecutionStep'; key: string}>;
  } | null;
};
