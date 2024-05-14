// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

<<<<<<< HEAD
export type RunTimelineFragment = {
  __typename: 'Run';
  id: string;
  pipelineName: string;
  status: Types.RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    id: string;
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
};

export type UnterminatedRunTimelineQueryVariables = Types.Exact<{
  inProgressFilter: Types.RunsFilter;
  limit: Types.Scalars['Int']['input'];
=======
export type UnterminatedRunTimelineQueryVariables = Types.Exact<{
  inProgressFilter: Types.RunsFilter;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
>>>>>>> d79d3b98e5f90f1e08688d5e62dda456e043b051
}>;

export type UnterminatedRunTimelineQuery = {
  __typename: 'Query';
  unterminated:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          pipelineName: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
        }>;
      };
};

<<<<<<< HEAD
export type TerminatedRunTimelineQueryVariables = Types.Exact<{
  terminatedFilter: Types.RunsFilter;
  limit: Types.Scalars['Int']['input'];
}>;

export type TerminatedRunTimelineQuery = {
=======
export type TerimatedRunTimelineQueryVariables = Types.Exact<{
  terminatedFilter: Types.RunsFilter;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;

export type TerimatedRunTimelineQuery = {
>>>>>>> d79d3b98e5f90f1e08688d5e62dda456e043b051
  __typename: 'Query';
  terminated:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          pipelineName: string;
          status: Types.RunStatus;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
        }>;
      };
};

export type FutureTicksQueryVariables = Types.Exact<{
  tickCursor?: Types.InputMaybe<Types.Scalars['Float']['input']>;
  ticksUntil?: Types.InputMaybe<Types.Scalars['Float']['input']>;
}>;

export type FutureTicksQuery = {
  __typename: 'Query';
  workspaceOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
          name: string;
          loadStatus: Types.RepositoryLocationLoadStatus;
          displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
          locationOrLoadError:
            | {__typename: 'PythonError'}
            | {
                __typename: 'RepositoryLocation';
                id: string;
                name: string;
                repositories: Array<{
                  __typename: 'Repository';
                  id: string;
                  name: string;
                  pipelines: Array<{
                    __typename: 'Pipeline';
                    id: string;
                    name: string;
                    isJob: boolean;
                  }>;
                  schedules: Array<{
                    __typename: 'Schedule';
                    id: string;
                    name: string;
                    pipelineName: string;
                    executionTimezone: string | null;
                    scheduleState: {
                      __typename: 'InstigationState';
                      id: string;
                      status: Types.InstigationStatus;
                    };
                    futureTicks: {
                      __typename: 'DryRunInstigationTicks';
                      results: Array<{
                        __typename: 'DryRunInstigationTick';
                        timestamp: number | null;
                      }>;
                    };
                  }>;
                }>;
              }
            | null;
        }>;
      };
};
