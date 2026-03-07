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
          assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
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

export const RunReExecutionQueryVersion = '78160a0b46e2b545a3aaf41800f7314d387363ce25ae1128e1c40ca269e56365';
