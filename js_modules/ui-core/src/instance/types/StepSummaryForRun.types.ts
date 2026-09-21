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

export type StepEventStatus = 'FAILURE' | 'IN_PROGRESS' | 'SKIPPED' | 'SUCCESS';

export type StepSummaryForRunQueryVariables = Exact<{
  runId: string;
}>;

export type StepSummaryForRunQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        status: Types.RunStatus;
        stepStats: Array<{
          __typename: 'RunStepStats';
          endTime: number | null;
          stepKey: string;
          status: Types.StepEventStatus | null;
        }>;
      }
    | {__typename: 'RunNotFoundError'};
};

export const StepSummaryForRunQueryVersion = '2890d0cd46c1f4d8b350a5fec57a0558ac3054e0ca93278998d66a54b2ebedbd';
