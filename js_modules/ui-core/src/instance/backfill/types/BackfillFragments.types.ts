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

export type PartitionSetForBackfillTableFragment = {
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
};

export type BackfillTerminationDialogBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  status: Types.BulkActionStatus;
  isAssetBackfill: boolean;
};

export type BackfillStepStatusDialogBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  partitionNames: Array<string> | null;
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
};

export type BackfillActionsBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  hasCancelPermission: boolean;
  hasResumePermission: boolean;
  isAssetBackfill: boolean;
  status: Types.BulkActionStatus;
  partitionNames: Array<string> | null;
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
};
