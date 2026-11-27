/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetKeyInput = {
  path: Array<string>;
};

export type SingleNonSdaAssetQueryVariables = Exact<{
  input: Types.AssetKeyInput;
}>;

export type SingleNonSdaAssetQuery = {
  __typename: 'Query';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        assetMaterializations: Array<{
          __typename: 'MaterializationEvent';
          runId: string;
          stepKey: string | null;
          timestamp: string;
        }>;
      }
    | {__typename: 'AssetNotFoundError'};
};
