// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

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
    name: string;
    pipelineName: string;
    repositoryOrigin: {
      __typename: 'RepositoryOrigin';
      repositoryName: string;
      repositoryLocationName: string;
    };
  } | null;
};
