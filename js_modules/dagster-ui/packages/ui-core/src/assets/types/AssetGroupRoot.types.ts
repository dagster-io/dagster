// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGroupMetadataQueryVariables = Types.Exact<{
  selector: Types.AssetGroupSelector;
}>;

export type AssetGroupMetadataQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    autoMaterializePolicy: {__typename: 'AutoMaterializePolicy'} | null;
  }>;
};

export const AssetGroupMetadataQueryVersion = '260d747ab8d454c1fe55a5a5fa6e11a548a301ea44740566c0c43756cca363eb';
