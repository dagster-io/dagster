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
