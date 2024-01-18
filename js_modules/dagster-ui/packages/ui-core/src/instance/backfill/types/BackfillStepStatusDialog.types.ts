// Generated GraphQL types, do not edit manually.
import * as Types from '../../../graphql/types';

export type BackfillStepStatusDialogBackfillFragment = {
  __typename: 'PartitionBackfill';
  id: string;
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
