// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: NavAssetFragment
// ====================================================

export interface NavAssetFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface NavAssetFragment {
  __typename: "AssetDefinition";
  id: string;
  assetKey: NavAssetFragment_assetKey;
  jobName: string | null;
}
