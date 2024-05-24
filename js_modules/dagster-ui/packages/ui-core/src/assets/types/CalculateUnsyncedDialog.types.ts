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
    isSource: boolean;
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
