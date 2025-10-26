// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetPermissionsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type AssetPermissionsQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        hasMaterializePermission: boolean;
        hasWipePermission: boolean;
        hasReportRunlessAssetEventPermission: boolean;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const AssetPermissionsQueryVersion = 'ff8b09ce270b20e67a0b552f66238f6705e12b79fdbff05b24a8dc3dcbf53ef0';
