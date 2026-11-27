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

export type AssetMaterializationUpstreamTableFragment = {
  __typename: 'AssetNode';
  id: string;
  assetMaterializationUsedData: Array<{
    __typename: 'MaterializationUpstreamDataVersion';
    timestamp: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    downstreamAssetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};

export type MaterializationUpstreamDataVersionFragment = {
  __typename: 'MaterializationUpstreamDataVersion';
  timestamp: string;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  downstreamAssetKey: {__typename: 'AssetKey'; path: Array<string>};
};

export type AssetMaterializationUpstreamQueryVariables = Exact<{
  assetKey: Types.AssetKeyInput;
  timestamp: string;
}>;

export type AssetMaterializationUpstreamQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        assetMaterializationUsedData: Array<{
          __typename: 'MaterializationUpstreamDataVersion';
          timestamp: string;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          downstreamAssetKey: {__typename: 'AssetKey'; path: Array<string>};
        }>;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const AssetMaterializationUpstreamQueryVersion = '6d185ba2c901fddec7845a056cd1be84f2e00e3284d4570da09ca9c552383e9b';
