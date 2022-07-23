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
  graphName: string | null;
  jobNames: string[];
  opNames: string[];
  description: string | null;
  computeKind: string | null;
  assetKey: AssetNodeFragment_assetKey;
}
