/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

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

export type HillpointeJobTimingsQueryVariables = Exact<{
  after: number;
}>;

export type HillpointeJobTimingsQuery = {
  __typename: 'Query';
  runsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          pipelineName: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryLocationName: string;
          } | null;
        }>;
      };
};

export type HillpointeJobRunStatsQueryVariables = Exact<{
  job: string;
}>;

export type HillpointeJobRunStatsQuery = {
  __typename: 'Query';
  runsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          status: Types.RunStatus;
          stats:
            | {__typename: 'PythonError'}
            | {__typename: 'RunStatsSnapshot'; id: string; materializations: number};
        }>;
      };
};
