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

export type TypeListContainerQueryVariables = Exact<{
  pipelineSelector: Types.PipelineSelector;
}>;

export type TypeListContainerQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        isJob: boolean;
        name: string;
        dagsterTypes: Array<
          | {
              __typename: 'ListDagsterType';
              name: string | null;
              isBuiltin: boolean;
              displayName: string;
              description: string | null;
            }
          | {
              __typename: 'NullableDagsterType';
              name: string | null;
              isBuiltin: boolean;
              displayName: string;
              description: string | null;
            }
          | {
              __typename: 'RegularDagsterType';
              name: string | null;
              isBuiltin: boolean;
              displayName: string;
              description: string | null;
            }
        >;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export const TypeListContainerQueryVersion = 'c92c874af7b1e7be221281fa265743a9c426f909ffc7500f302540ef9a6cf8f2';
