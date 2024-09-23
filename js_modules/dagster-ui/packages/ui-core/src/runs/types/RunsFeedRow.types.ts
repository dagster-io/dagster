// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunsFeedTableEntryFragment_PartitionBackfill = {
  __typename: 'PartitionBackfill';
  partitionSetName: string | null;
  hasCancelPermission: boolean;
  hasResumePermission: boolean;
  isAssetBackfill: boolean;
  numCancelable: number;
  id: string;
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
};

export type RunsFeedTableEntryFragment_Run = {
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
};

export type RunsFeedTableEntryFragment =
  | RunsFeedTableEntryFragment_PartitionBackfill
  | RunsFeedTableEntryFragment_Run;
