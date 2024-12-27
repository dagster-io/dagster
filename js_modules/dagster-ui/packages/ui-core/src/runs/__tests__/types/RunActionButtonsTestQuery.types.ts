// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type RunActionButtonsTestQueryVariables = Types.Exact<{[key: string]: never}>;

export type RunActionButtonsTestQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        parentPipelineSnapshotId: string | null;
        runConfigYaml: string;
        canTerminate: boolean;
        hasReExecutePermission: boolean;
        hasTerminatePermission: boolean;
        hasDeletePermission: boolean;
        hasRunMetricsEnabled: boolean;
        status: Types.RunStatus;
        mode: string;
        rootRunId: string | null;
        parentRunId: string | null;
        pipelineName: string;
        solidSelection: Array<string> | null;
        pipelineSnapshotId: string | null;
        stepKeysToExecute: Array<string> | null;
        updateTime: number | null;
        startTime: number | null;
        endTime: number | null;
        hasConcurrencyKeySlots: boolean;
        repositoryOrigin: {
          __typename: 'RepositoryOrigin';
          id: string;
          repositoryName: string;
          repositoryLocationName: string;
        } | null;
        tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        assetCheckSelection: Array<{
          __typename: 'AssetCheckhandle';
          name: string;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
        }> | null;
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

export const RunActionButtonsTestQueryVersion = '5d358c3360e683549b885108c3dbb7c1d21d8afd790a5ee963e6e9640ccdbfe8';
