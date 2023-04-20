// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunTableRunNewFragment = {
  __typename: 'Run';
  id: string;
  status: Types.RunStatus;
  stepKeysToExecute: Array<string> | null;
  canTerminate: boolean;
  hasReExecutePermission: boolean;
  hasTerminatePermission: boolean;
  hasDeletePermission: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  solidSelection: Array<string> | null;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  repositoryOrigin: {
    __typename: 'RepositoryOrigin';
    id: string;
    repositoryName: string;
    repositoryLocationName: string;
  } | null;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};
