// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type SingleBackfillCountsQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type SingleBackfillCountsQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {
        __typename: 'PartitionBackfill';
        id: string;
        partitionStatusCounts: Array<{
          __typename: 'PartitionStatusCounts';
          runStatus: Types.RunStatus;
          count: number;
        }>;
      }
    | {__typename: 'PythonError'};
};

export type SingleBackfillQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type SingleBackfillQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {
        __typename: 'PartitionBackfill';
        id: string;
        unfinishedRuns: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          status: Types.RunStatus;
        }>;
      }
    | {__typename: 'PythonError'};
};

export type UnfinishedRunsForBackfillFragment = {
  __typename: 'Run';
  id: string;
  runId: string;
  status: Types.RunStatus;
};
