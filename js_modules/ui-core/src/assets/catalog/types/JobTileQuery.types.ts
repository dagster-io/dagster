/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: string;
};

export type AssetKeyInput = {
  path: Array<string>;
};

export type PipelineSelector = {
  assetCheckSelection?: Array<AssetCheckHandleInput> | null | undefined;
  assetSelection?: Array<AssetKeyInput> | null | undefined;
  pipelineName: string;
  repositoryLocationName: string;
  repositoryName: string;
  solidSelection?: Array<string> | null | undefined;
};

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type JobTileQueryVariables = Exact<{
  pipelineSelector: Types.PipelineSelector;
}>;

export type JobTileQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        runs: Array<{
          __typename: 'Run';
          id: string;
          runId: string;
          runStatus: Types.RunStatus;
          startTime: number | null;
        }>;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export const JobTileQueryVersion = '6fd1bb8a16c8bd5fff0fb75f6608d5402a426d5c2763fefcb61d60e94ff0a3e8';
