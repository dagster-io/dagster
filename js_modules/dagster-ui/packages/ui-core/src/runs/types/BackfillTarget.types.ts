// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type BackfillTargetFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  partitionNames: Array<string> | null;
  numPartitions: number | null;
  partitionSetName: string | null;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
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
