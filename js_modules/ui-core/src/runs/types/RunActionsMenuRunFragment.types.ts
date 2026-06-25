// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunActionsMenuRunFragment = {
  __typename: 'Run';
  id: string;
  assetCheckSelectionCount: number;
  hasReExecutePermission: boolean;
  hasTerminatePermission: boolean;
  hasDeletePermission: boolean;
  canTerminate: boolean;
  mode: string;
  status: Types.RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  hasRunMetricsEnabled: boolean;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    id: string;
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
};
