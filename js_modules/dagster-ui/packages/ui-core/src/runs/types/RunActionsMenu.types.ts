// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunActionsMenuRunFragment = {
  __typename: 'Run';
  id: string;
  hasReExecutePermission: boolean;
  hasTerminatePermission: boolean;
  hasDeletePermission: boolean;
  canTerminate: boolean;
  mode: string;
  status: Types.RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  assetCheckSelection: Array<{
    __typename: 'AssetCheckhandle';
    name: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }> | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
};

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
        repositoryOrigin: {
          __typename: 'RepositoryOrigin';
          id: string;
          repositoryName: string;
          repositoryLocationName: string;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const PipelineEnvironmentQueryVersion = '762f0cd2639e98c470cecdb3d2f7ca4609bd77be7f916e0134021bd0b589da59';
