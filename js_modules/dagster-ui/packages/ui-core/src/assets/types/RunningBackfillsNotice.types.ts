// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunningBackfillsNoticeQueryVariables = Types.Exact<{[key: string]: never}>;

export type RunningBackfillsNoticeQuery = {
  __typename: 'Query';
  partitionBackfillsOrError:
    | {
        __typename: 'PartitionBackfills';
        results: Array<{
          __typename: 'PartitionBackfill';
          id: string;
          partitionSetName: string | null;
        }>;
      }
    | {__typename: 'PythonError'};
};
