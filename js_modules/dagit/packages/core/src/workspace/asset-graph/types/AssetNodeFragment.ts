/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeFragment
// ====================================================

export interface AssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  assetKey: AssetNodeFragment_assetKey;
}
