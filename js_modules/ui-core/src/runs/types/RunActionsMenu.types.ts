/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PipelineEnvironmentQueryVariables = Exact<{
  runId: string;
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

export const PipelineEnvironmentQueryVersion = '6bd5598ee7119d0e6f403247c78c1d0670e198985b809a4bf1ddafe81c534d7e';
