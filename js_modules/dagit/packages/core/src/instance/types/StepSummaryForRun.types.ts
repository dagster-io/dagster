// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type StepSummaryForRunQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
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
