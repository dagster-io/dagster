// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SnapshotWarningAssetFragment
// ====================================================

export interface SnapshotWarningAssetFragment_key {
  __typename: "AssetKey";
  path: string[];
}

export interface SnapshotWarningAssetFragment_mostRecentMaterialization_materializationEvent {
  __typename: "StepMaterializationEvent";
  timestamp: string;
}

export interface SnapshotWarningAssetFragment_mostRecentMaterialization {
  __typename: "AssetMaterialization";
  materializationEvent: SnapshotWarningAssetFragment_mostRecentMaterialization_materializationEvent;
}

export interface SnapshotWarningAssetFragment_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  timestamp: string;
}

export interface SnapshotWarningAssetFragment_assetMaterializations {
  __typename: "AssetMaterialization";
  materializationEvent: SnapshotWarningAssetFragment_assetMaterializations_materializationEvent;
}

export interface SnapshotWarningAssetFragment {
  __typename: "Asset";
  id: string;
  key: SnapshotWarningAssetFragment_key;
  mostRecentMaterialization: SnapshotWarningAssetFragment_mostRecentMaterialization[];
  assetMaterializations: SnapshotWarningAssetFragment_assetMaterializations[];
}
