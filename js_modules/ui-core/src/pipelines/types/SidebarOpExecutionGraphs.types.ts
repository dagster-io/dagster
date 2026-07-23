/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

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

export type StepEventStatus = 'FAILURE' | 'IN_PROGRESS' | 'SKIPPED' | 'SUCCESS';

export type SidebarOpGraphsQueryVariables = Exact<{
  selector: Types.PipelineSelector;
  handleID: string;
}>;

export type SidebarOpGraphsQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        name: string;
        solidHandle: {
          __typename: 'SolidHandle';
          stepStats:
            | {
                __typename: 'SolidStepStatsConnection';
                nodes: Array<{
                  __typename: 'RunStepStats';
                  runId: string;
                  startTime: number | null;
                  endTime: number | null;
                  status: Types.StepEventStatus | null;
                }>;
              }
            | {__typename: 'SolidStepStatusUnavailableError'}
            | null;
        } | null;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export const SidebarOpGraphsQueryVersion = '3feca8de1ac2e1f479a0a6b88b76e731da4162cb717f7174e5f232527cc6ce52';
