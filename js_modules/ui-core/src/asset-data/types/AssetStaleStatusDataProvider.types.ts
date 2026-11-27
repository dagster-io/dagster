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

export type StaleCauseCategory = 'CODE' | 'DATA' | 'DEPENDENCIES';

export type StaleStatus = 'FRESH' | 'MISSING' | 'STALE';

export type AssetStaleDataFragment = {
  __typename: 'AssetNode';
  id: string;
  staleStatus: Types.StaleStatus | null;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  staleCauses: Array<{
    __typename: 'StaleCause';
    reason: string;
    category: Types.StaleCauseCategory;
    key: {__typename: 'AssetKey'; path: Array<string>};
    dependency: {__typename: 'AssetKey'; path: Array<string>} | null;
  }>;
};

export type AssetStaleStatusDataQueryVariables = Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetStaleStatusDataQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    staleStatus: Types.StaleStatus | null;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    staleCauses: Array<{
      __typename: 'StaleCause';
      reason: string;
      category: Types.StaleCauseCategory;
      key: {__typename: 'AssetKey'; path: Array<string>};
      dependency: {__typename: 'AssetKey'; path: Array<string>} | null;
    }>;
  }>;
};

export const AssetStaleStatusDataQueryVersion = '0168440bb72ae79664e8ba33f41a85f99398d0838b0baaa611b16a4dbb15b004';
