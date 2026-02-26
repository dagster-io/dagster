// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CheckBackfillStatusQueryVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type CheckBackfillStatusQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {__typename: 'PartitionBackfill'; id: string; status: Types.BulkActionStatus}
    | {__typename: 'PythonError'};
};

export const CheckBackfillStatusVersion = 'd102ea2a2b731fdbefb7b6762c94aa0a8468b7977c9143cec33a8ea900f2e469';
