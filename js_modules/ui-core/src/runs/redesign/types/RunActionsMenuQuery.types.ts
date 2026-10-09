/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type RunActionsMenuDetailsFragment = {
  __typename: 'Run';
  id: string;
  parentPipelineSnapshotId: string | null;
  runConfigYaml: string;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  assetCheckSelection: Array<{
    __typename: 'AssetCheckhandle';
    name: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }> | null;
  executionPlan: {
    __typename: 'ExecutionPlan';
    assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  } | null;
};

export type RunActionsMenuQueryVariables = Exact<{
  runId: string;
}>;

export type RunActionsMenuQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        parentPipelineSnapshotId: string | null;
        runConfigYaml: string;
        assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
        assetCheckSelection: Array<{
          __typename: 'AssetCheckhandle';
          name: string;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
        }> | null;
        executionPlan: {
          __typename: 'ExecutionPlan';
          assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
};

export const RunActionsMenuQueryVersion = '4229b82cf3ae0a33b2a6ad425b72edb6a09d380fd8a3141dd394200cc5748298';
