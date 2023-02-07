// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunningBackfillsNoticeQueryVariables = Types.Exact<{[key: string]: never}>;

export type RunningBackfillsNoticeQuery = {
  __typename: 'DagitQuery';
  partitionBackfillsOrError:
    | {
        __typename: 'PartitionBackfills';
        results: Array<{
          __typename: 'PartitionBackfill';
          partitionSetName: string | null;
          backfillId: string;
        }>;
      }
    | {__typename: 'PythonError'};
};
