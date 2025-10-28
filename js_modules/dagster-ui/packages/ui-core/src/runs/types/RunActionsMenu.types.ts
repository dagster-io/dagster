// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PipelineEnvironmentQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type PipelineEnvironmentQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        pipelineName: string;
        pipelineSnapshotId: string | null;
        runConfigYaml: string;
        parentPipelineSnapshotId: string | null;
        hasRunMetricsEnabled: boolean;
        repositoryOrigin: {
          __typename: 'RepositoryOrigin';
          id: string;
          repositoryName: string;
          repositoryLocationName: string;
        } | null;
        executionPlan: {
          __typename: 'ExecutionPlan';
          assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const PipelineEnvironmentQueryVersion = '159c70bc524e11bca5337e75b0f9a5c9d4e1ad96cf72d98e5e9ff6f9e4bde6b0';
