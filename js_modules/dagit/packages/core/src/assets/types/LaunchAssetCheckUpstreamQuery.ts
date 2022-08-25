/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LaunchAssetCheckUpstreamQuery
// ====================================================

export interface LaunchAssetCheckUpstreamQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LaunchAssetCheckUpstreamQuery_assetNodes_assetMaterializations {
  __typename: "MaterializationEvent";
  runId: string;
}

export interface LaunchAssetCheckUpstreamQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: LaunchAssetCheckUpstreamQuery_assetNodes_assetKey;
  opNames: string[];
  graphName: string | null;
  assetMaterializations: LaunchAssetCheckUpstreamQuery_assetNodes_assetMaterializations[];
}

export interface LaunchAssetCheckUpstreamQuery {
  assetNodes: LaunchAssetCheckUpstreamQuery_assetNodes[];
}

export interface LaunchAssetCheckUpstreamQueryVariables {
  assetKeys: AssetKeyInput[];
}
