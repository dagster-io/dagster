/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: GraphExplorerAssetNodeFragment
// ====================================================

export interface GraphExplorerAssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface GraphExplorerAssetNodeFragment {
  __typename: "AssetNode";
  opName: string | null;
  assetKey: GraphExplorerAssetNodeFragment_assetKey;
}
