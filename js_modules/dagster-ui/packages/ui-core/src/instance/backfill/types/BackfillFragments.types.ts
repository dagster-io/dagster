// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillTerminationDialogBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  status: Types.BulkActionStatus;
  isAssetBackfill: boolean;
  numCancelable: number;
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
  numCancelable: number;
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
