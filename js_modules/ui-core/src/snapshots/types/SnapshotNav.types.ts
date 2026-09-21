/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SnapshotQueryVariables = Exact<{
  snapshotId: string;
}>;

export type SnapshotQuery = {
  __typename: 'Query';
  pipelineSnapshotOrError:
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PipelineSnapshot'; id: string; parentSnapshotId: string | null}
    | {__typename: 'PipelineSnapshotNotFoundError'}
    | {__typename: 'PythonError'};
};

export const SnapshotQueryVersion = '6ada4abd4592a558d98b2557ec511e87c9420bab5cbc155ec8473c55bd820a7a';
