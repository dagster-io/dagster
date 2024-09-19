// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetMaterializationUpstreamTableFragment = {
  __typename: 'AssetNode';
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

export type AssetMaterializationUpstreamQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  timestamp: Types.Scalars['String']['input'];
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

export const AssetMaterializationUpstreamQueryVersion = '754bab88738acc8d310c71f577ac3cf06dc57950bb1f98a18844e6e00bae756d';
