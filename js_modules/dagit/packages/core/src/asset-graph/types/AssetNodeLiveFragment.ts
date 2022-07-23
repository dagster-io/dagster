/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeLiveFragment
// ====================================================

export interface AssetNodeLiveFragment_repository {
  __typename: "Repository";
  id: string;
}

export interface AssetNodeLiveFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations {
  __typename: "MaterializationEvent";
  timestamp: string;
  runId: string;
}

export interface AssetNodeLiveFragment {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  repository: AssetNodeLiveFragment_repository;
  assetKey: AssetNodeLiveFragment_assetKey;
  assetMaterializations: AssetNodeLiveFragment_assetMaterializations[];
}
