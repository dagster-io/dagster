// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ScheduleTickConfigQueryVariables = Types.Exact<{
  scheduleSelector: Types.ScheduleSelector;
  tickTimestamp: Types.Scalars['Int'];
}>;

export type ScheduleTickConfigQuery = {
  __typename: 'DagitQuery';
  scheduleOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Schedule';
        id: string;
        futureTick: {
          __typename: 'FutureInstigationTick';
          evaluationResult: {
            __typename: 'TickEvaluation';
            skipReason: string | null;
            runRequests: Array<{
              __typename: 'RunRequest';
              runKey: string | null;
              runConfigYaml: string;
              tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
            } | null> | null;
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
  } | null> | null;
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
