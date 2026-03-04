// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type QueuedRunCriteriaQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
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
