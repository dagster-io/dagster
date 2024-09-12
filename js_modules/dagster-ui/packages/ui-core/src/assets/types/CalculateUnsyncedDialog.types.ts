// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetStaleStatusQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetStaleStatusQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    isMaterializable: boolean;
    staleStatus: Types.StaleStatus | null;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    partitionStats: {
      __typename: 'PartitionStats';
      numMaterialized: number;
      numMaterializing: number;
      numPartitions: number;
      numFailed: number;
    } | null;
  }>;
};

export const AssetStaleStatusQueryVersion = '2c0792a380368dfd0b6c892bd7c18f86bb34e599a2f8b020852b4a6285defa37';
