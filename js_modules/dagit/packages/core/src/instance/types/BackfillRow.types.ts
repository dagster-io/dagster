// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleBackfillQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String'];
}>;

export type SingleBackfillQuery = {
  __typename: 'DagitQuery';
  partitionBackfillOrError:
    | {
        __typename: 'PartitionBackfill';
        partitionStatuses: {
          __typename: 'PartitionStatuses';
          results: Array<{
            __typename: 'PartitionStatus';
            id: string;
            partitionName: string;
            runId: string | null;
            runStatus: Types.RunStatus | null;
          }>;
        };
      }
    | {__typename: 'PythonError'};
};

export type PartitionStatusesForBackfillFragment = {
  __typename: 'PartitionStatuses';
  results: Array<{
    __typename: 'PartitionStatus';
    id: string;
    partitionName: string;
    runId: string | null;
    runStatus: Types.RunStatus | null;
  }>;
};
