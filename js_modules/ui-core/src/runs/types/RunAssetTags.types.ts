/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunAssetsQueryVariables = Exact<{
  runId: string;
}>;

export type RunAssetsQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        assets: Array<{
          __typename: 'Asset';
          id: string;
          key: {__typename: 'AssetKey'; path: Array<string>};
        }>;
      }
    | {__typename: 'RunNotFoundError'};
};

export const RunAssetsQueryVersion = '53c1e7814d451dfd58fb2427dcb326a1e9628c8bbc91b3b9c76f8d6c7b75e278';
