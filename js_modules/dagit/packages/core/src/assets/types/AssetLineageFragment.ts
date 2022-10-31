/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetLineageFragment
// ====================================================

export interface AssetLineageFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLineageFragment {
  __typename: "AssetLineageInfo";
  assetKey: AssetLineageFragment_assetKey;
  partitions: string[];
}
