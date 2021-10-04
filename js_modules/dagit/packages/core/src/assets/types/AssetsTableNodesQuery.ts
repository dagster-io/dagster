// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetsTableNodesQuery
// ====================================================

export interface AssetsTableNodesQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetsTableNodesQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobName: string | null;
  description: string | null;
  assetKey: AssetsTableNodesQuery_assetNodes_assetKey;
}

export interface AssetsTableNodesQuery {
  assetNodes: AssetsTableNodesQuery_assetNodes[];
}
