// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillStepStatusDialogContentQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type BackfillStepStatusDialogContentQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {
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
      }
    | {__typename: 'PythonError'};
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

export const BackfillStepStatusDialogContentQueryVersion = 'd3be1982810b3fa39b1a07621e3575e028a9ea97e276eeaf551c6535291d902a';
