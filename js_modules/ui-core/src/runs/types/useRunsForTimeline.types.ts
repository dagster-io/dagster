/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ExecutionTag = {
  key: string;
  value: string;
};

export type InstigationStatus = 'RUNNING' | 'STOPPED';

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

export type RunsFilter = {
  createdAfter?: number | null | undefined;
  createdBefore?: number | null | undefined;
  mode?: string | null | undefined;
  pipelineName?: string | null | undefined;
  runIds?: Array<string | null | undefined> | null | undefined;
  snapshotId?: string | null | undefined;
  statuses?: Array<RunStatus> | null | undefined;
  tags?: Array<ExecutionTag> | null | undefined;
  updatedAfter?: number | null | undefined;
  updatedBefore?: number | null | undefined;
};

export type RunTimelineFragment = {
  __typename: 'Run';
  id: string;
  pipelineName: string;
  externalJobSource: string | null;
  status: Types.RunStatus;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    id: string;
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
};

export type OngoingRunTimelineQueryVariables = Exact<{
  inProgressFilter: Types.RunsFilter;
  limit: number;
  cursor?: string | null | undefined;
}>;

export type OngoingRunTimelineQuery = {
  __typename: 'Query';
  ongoing:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          pipelineName: string;
          externalJobSource: string | null;
          status: Types.RunStatus;
          creationTime: number;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
        }>;
      };
};

export type CompletedRunTimelineQueryVariables = Exact<{
  completedFilter: Types.RunsFilter;
  limit: number;
  cursor?: string | null | undefined;
}>;

export type CompletedRunTimelineQuery = {
  __typename: 'Query';
  completed:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          pipelineName: string;
          externalJobSource: string | null;
          status: Types.RunStatus;
          creationTime: number;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
        }>;
      };
};

export type FutureTicksQueryVariables = Exact<{
  tickCursor?: number | null | undefined;
  ticksUntil?: number | null | undefined;
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

export const OngoingRunTimelineQueryVersion = '7437e39dbde776b1bbaa231d1cfdd4611117e72eabd0f8fc9f64d13ec150c82b';

export const CompletedRunTimelineQueryVersion = '1f34f13f13209633691baabedf021000f45052a8cc5499108393013cae3e1f00';

export const FutureTicksQueryVersion = '9b947053273ecaa20ef19df02f0aa8e6f33b8a1628175987670e3c73a350e640';
