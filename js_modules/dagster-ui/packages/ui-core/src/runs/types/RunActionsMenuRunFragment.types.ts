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
  hasRunMetricsEnabled: boolean;
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
