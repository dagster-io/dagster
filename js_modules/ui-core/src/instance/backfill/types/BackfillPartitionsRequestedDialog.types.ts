/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillPartitionsDialogContentQueryVariables = Exact<{
  backfillId: string;
}>;

export type BackfillPartitionsDialogContentQuery = {
  __typename: 'Query';
  partitionBackfillOrError:
    | {__typename: 'BackfillNotFoundError'}
    | {__typename: 'PartitionBackfill'; id: string; partitionNames: Array<string> | null}
    | {__typename: 'PythonError'};
};

export const BackfillPartitionsDialogContentQueryVersion = '5d9656add9f2073f1bf82bd3b7ce31fdcf75221869cd80f90e0ac7ff820aebac';
