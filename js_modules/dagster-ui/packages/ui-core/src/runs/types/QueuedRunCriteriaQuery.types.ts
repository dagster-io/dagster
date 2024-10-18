// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type QueuedRunCriteriaQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type QueuedRunCriteriaQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        rootConcurrencyKeys: Array<string> | null;
        hasUnconstrainedRootNodes: boolean;
      }
    | {__typename: 'RunNotFoundError'};
};

export const QueuedRunCriteriaQueryVersion = 'da19aeed8a0a7e6f47619c6ba9efd721345481d8f08223282ea774e468400f21';
