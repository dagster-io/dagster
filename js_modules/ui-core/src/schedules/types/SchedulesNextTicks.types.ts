/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStatus = 'RUNNING' | 'STOPPED';

export type ScheduleSelector = {
  repositoryLocationName: string;
  repositoryName: string;
  scheduleName: string;
};

export type ScheduleNextFiveTicksFragment = {
  __typename: 'Schedule';
  id: string;
  name: string;
  executionTimezone: string | null;
  mode: string;
  solidSelection: Array<string | null> | null;
  pipelineName: string;
  scheduleState: {__typename: 'InstigationState'; id: string; status: Types.InstigationStatus};
  futureTicks: {
    __typename: 'DryRunInstigationTicks';
    results: Array<{__typename: 'DryRunInstigationTick'; timestamp: number | null}>;
  };
};

export type RepositoryForNextTicksFragment = {
  __typename: 'Repository';
  name: string;
  id: string;
  location: {__typename: 'RepositoryLocation'; id: string; name: string};
  schedules: Array<{
    __typename: 'Schedule';
    id: string;
    name: string;
    executionTimezone: string | null;
    mode: string;
    solidSelection: Array<string | null> | null;
    pipelineName: string;
    scheduleState: {__typename: 'InstigationState'; id: string; status: Types.InstigationStatus};
    futureTicks: {
      __typename: 'DryRunInstigationTicks';
      results: Array<{__typename: 'DryRunInstigationTick'; timestamp: number | null}>;
    };
  }>;
};

export type ScheduleTickConfigQueryVariables = Exact<{
  scheduleSelector: Types.ScheduleSelector;
  tickTimestamp: number;
}>;

export type ScheduleTickConfigQuery = {
  __typename: 'Query';
  scheduleOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Schedule';
        id: string;
        futureTick: {
          __typename: 'DryRunInstigationTick';
          evaluationResult: {
            __typename: 'TickEvaluation';
            skipReason: string | null;
            runRequests: Array<{
              __typename: 'RunRequest';
              runKey: string | null;
              runConfigYaml: string;
              tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
            }> | null;
            error: {
              __typename: 'PythonError';
              message: string;
              stack: Array<string>;
              errorChain: Array<{
                __typename: 'ErrorChainLink';
                isExplicitLink: boolean;
                error: {__typename: 'PythonError'; message: string; stack: Array<string>};
              }>;
            } | null;
          } | null;
        };
      }
    | {__typename: 'ScheduleNotFoundError'};
};

export type ScheduleFutureTickEvaluationResultFragment = {
  __typename: 'TickEvaluation';
  skipReason: string | null;
  runRequests: Array<{
    __typename: 'RunRequest';
    runKey: string | null;
    runConfigYaml: string;
    tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  }> | null;
  error: {
    __typename: 'PythonError';
    message: string;
    stack: Array<string>;
    errorChain: Array<{
      __typename: 'ErrorChainLink';
      isExplicitLink: boolean;
      error: {__typename: 'PythonError'; message: string; stack: Array<string>};
    }>;
  } | null;
};

export type ScheduleFutureTickRunRequestFragment = {
  __typename: 'RunRequest';
  runKey: string | null;
  runConfigYaml: string;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export const ScheduleTickConfigQueryVersion = 'acdec3206ff12d652fe6657c8c51202a65b652b9575625d1f024014bbb828788';
