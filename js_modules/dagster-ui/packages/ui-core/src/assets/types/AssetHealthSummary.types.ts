// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type GetAssetHealthQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type GetAssetHealthQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetHealth: {
      __typename: 'AssetHealth';
      assetHealth: Types.AssetHealthStatus;
      materializationStatus: Types.AssetHealthStatus;
      assetChecksStatus: Types.AssetHealthStatus;
      freshnessStatus: Types.AssetHealthStatus;
    } | null;
  }>;
};

export const GetAssetHealthVersion = '5416141b420dea60cd5eb905d8c0d9cab50bd8932013fc6702a15758d200f23c';
