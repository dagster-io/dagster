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
          assetSelection: Array<string>;
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

export const RunReExecutionQueryVersion = '6292ae2ffce17df5b8d31c3ef78356059e970c58b4271d1a9a6d21a0a09a10b0';
