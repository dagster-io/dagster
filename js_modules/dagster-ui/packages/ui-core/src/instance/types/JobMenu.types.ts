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
        tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
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

export const RunReExecutionQueryVersion = 'dba97848ec33219b3747bac51bb8fd3df5c37c662a47f1a8bd2563bfaa27c3f3';
