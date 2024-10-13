// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunReExecutionQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type RunReExecutionQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        status: Types.RunStatus;
        pipelineName: string;
        executionPlan: {
          __typename: 'ExecutionPlan';
          artifactsPersisted: boolean;
          steps: Array<{
            __typename: 'ExecutionStep';
            key: string;
            kind: Types.StepKind;
            inputs: Array<{
              __typename: 'ExecutionStepInput';
              dependsOn: Array<{__typename: 'ExecutionStep'; key: string; kind: Types.StepKind}>;
            }>;
          }>;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const RunReExecutionQueryVersion = '95f0a988be27f8d33377eec80eaac91bcbd709e73098e0b12f05f71c4f732077';
