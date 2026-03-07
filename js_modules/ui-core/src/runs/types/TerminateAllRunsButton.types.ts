// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TerminateRunIdsQueryVariables = Types.Exact<{
  filter: Types.RunsFilter;
}>;

export type TerminateRunIdsQuery = {
  __typename: 'Query';
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          canTerminate: boolean;
        }>;
      };
};

export const TerminateVersion = '67acf403eb320a93c9a9aa07f675a1557e0887d499cd5598f1d5ff360afc15c0';

export const TerminateRunIdsQueryVersion = 'd38573af47f3ab2f2b11d90cb85ce8426307e2384e67a5b20e2bf67d5c1054bb';
