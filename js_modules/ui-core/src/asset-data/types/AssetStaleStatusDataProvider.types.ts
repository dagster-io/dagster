// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

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

export type AssetStaleStatusDataQueryVariables = Types.Exact<{
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
