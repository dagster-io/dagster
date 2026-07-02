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

export type AssetsPermissionsQueryVariables = Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetsPermissionsQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    hasMaterializePermission: boolean;
    hasWipePermission: boolean;
    hasReportRunlessAssetEventPermission: boolean;
  }>;
};

export const AssetsPermissionsQueryVersion = 'ab77e79a165269b79bdd9768a816cdccfb6fe320b2abbc6d0e2b1deb307d4590';
