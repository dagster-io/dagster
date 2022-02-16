/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetMaterializationTimesQuery
// ====================================================

export interface AssetMaterializationTimesQuery_assetNodes_assetMaterializations {
  __typename: "MaterializationEvent";
  timestamp: string;
  runId: string;
}

export interface AssetMaterializationTimesQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetMaterializations: AssetMaterializationTimesQuery_assetNodes_assetMaterializations[];
}

export interface AssetMaterializationTimesQuery {
  assetNodes: AssetMaterializationTimesQuery_assetNodes[];
}

export interface AssetMaterializationTimesQueryVariables {
  assetKeys?: AssetKeyInput[] | null;
}
