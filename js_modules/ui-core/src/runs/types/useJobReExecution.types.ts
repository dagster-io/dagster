/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type BulkActionStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'COMPLETED'
  | 'COMPLETED_FAILED'
  | 'COMPLETED_SUCCESS'
  | 'FAILED'
  | 'FAILING'
  | 'REQUESTED';

export type CheckBackfillStatusQueryVariables = Exact<{
  backfillId: string;
}>;

export type CheckBackfillStatusQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {__typename: 'PartitionBackfill'; id: string; status: Types.BulkActionStatus}
    | {__typename: 'PythonError'};
};

export const CheckBackfillStatusVersion = 'd102ea2a2b731fdbefb7b6762c94aa0a8468b7977c9143cec33a8ea900f2e469';
