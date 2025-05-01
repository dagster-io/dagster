// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

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

export type OngoingRunTimelineQueryVariables = Types.Exact<{
  inProgressFilter: Types.RunsFilter;
  limit: Types.Scalars['Int']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
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

export type CompletedRunTimelineQueryVariables = Types.Exact<{
  completedFilter: Types.RunsFilter;
  limit: Types.Scalars['Int']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
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
