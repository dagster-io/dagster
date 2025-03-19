// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillTerminationDialogBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  status: Types.BulkActionStatus;
  isAssetBackfill: boolean;
  numCancelable: number;
};

export type BackfillTableFragmentForStepStatusDialogFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  partitionSet: {__typename: 'PartitionSet'; id: string} | null;
};

export type BackfillActionsBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  hasCancelPermission: boolean;
  hasResumePermission: boolean;
  isAssetBackfill: boolean;
  status: Types.BulkActionStatus;
  numCancelable: number;
  partitionSet: {__typename: 'PartitionSet'; id: string} | null;
};
