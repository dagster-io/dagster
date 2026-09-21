/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type QueuedRunCriteriaQueryVariables = Exact<{
  runId: string;
}>;

export type QueuedRunCriteriaQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    poolConfig: {__typename: 'PoolConfig'; poolGranularity: string | null} | null;
  };
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        rootConcurrencyKeys: Array<string> | null;
        hasUnconstrainedRootNodes: boolean;
        allPools: Array<string> | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const QueuedRunCriteriaQueryVersion = 'f925e1576792948317528a64856c3c020591feefac39f1aaebb3092d0fd3cd0b';
