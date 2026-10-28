/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
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

export type MobileJobAssetsQueryVariables = Exact<{
  params: Types.PipelineSelector;
}>;


export type MobileJobAssetsQuery = { __typename: 'Query', assetNodes: Array<{ __typename: 'AssetNode', id: string, assetKey: { __typename: 'AssetKey', path: Array<string> } }> };

export type MobileRecentRunsQueryVariables = Exact<{
  limit: number;
}>;


export type MobileRecentRunsQuery = { __typename: 'Query', runsOrError:
    | { __typename: 'InvalidPipelineRunsFilterError' }
    | { __typename: 'PythonError' }
    | { __typename: 'Runs', results: Array<{ __typename: 'Run', id: string, runId: string, status: Types.RunStatus, pipelineName: string, startTime: number | null, endTime: number | null, repositoryOrigin: { __typename: 'RepositoryOrigin', id: string, repositoryName: string, repositoryLocationName: string } | null }> }
   };
