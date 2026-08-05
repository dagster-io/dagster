/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type RunStatusOnlyQueryVariables = Exact<{
  runId: string;
}>;

export type RunStatusOnlyQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'Run'; id: string; status: Types.RunStatus}
    | {__typename: 'RunNotFoundError'};
};

export const RunStatusOnlyQueryVersion = 'e0000c8f2600dbe29f305febb04cca005e08da6a7ce03ec20476c59d607495c0';
