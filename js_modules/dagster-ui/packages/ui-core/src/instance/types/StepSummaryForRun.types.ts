// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type StepSummaryForRunQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
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
