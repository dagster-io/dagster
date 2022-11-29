/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionHealthQuery
// ====================================================

export interface PartitionHealthQuery_assetNodeOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionKeysByDimension {
  __typename: "DimensionPartitionKeys";
  name: string;
  partitionKeys: string[];
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationStatus_MaterializationStatusGroupedByDimension {
  __typename: "MaterializationStatusGroupedByDimension";
  materializationStatusGrouped: boolean[][];
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationStatus_MaterializationStatusSingleDimension {
  __typename: "MaterializationStatusSingleDimension";
  materializationStatus: boolean[];
}

export type PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationStatus = PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationStatus_MaterializationStatusGroupedByDimension | PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationStatus_MaterializationStatusSingleDimension;

export interface PartitionHealthQuery_assetNodeOrError_AssetNode {
  __typename: "AssetNode";
  id: string;
  partitionKeysByDimension: PartitionHealthQuery_assetNodeOrError_AssetNode_partitionKeysByDimension[];
  partitionMaterializationStatus: PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationStatus;
}

export type PartitionHealthQuery_assetNodeOrError = PartitionHealthQuery_assetNodeOrError_AssetNotFoundError | PartitionHealthQuery_assetNodeOrError_AssetNode;

export interface PartitionHealthQuery {
  assetNodeOrError: PartitionHealthQuery_assetNodeOrError;
}

export interface PartitionHealthQueryVariables {
  assetKey: AssetKeyInput;
}
