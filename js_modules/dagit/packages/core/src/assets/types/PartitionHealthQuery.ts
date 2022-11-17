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

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountGroupedByDimension {
  __typename: "MaterializationCountGroupedByDimension";
  materializationCountsGrouped: number[][];
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountSingleDimension {
  __typename: "MaterializationCountSingleDimension";
  materializationCounts: number[];
}

export type PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts = PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountGroupedByDimension | PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountSingleDimension;

export interface PartitionHealthQuery_assetNodeOrError_AssetNode {
  __typename: "AssetNode";
  id: string;
  partitionKeysByDimension: PartitionHealthQuery_assetNodeOrError_AssetNode_partitionKeysByDimension[];
  partitionMaterializationCounts: PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts;
}

export type PartitionHealthQuery_assetNodeOrError = PartitionHealthQuery_assetNodeOrError_AssetNotFoundError | PartitionHealthQuery_assetNodeOrError_AssetNode;

export interface PartitionHealthQuery {
  assetNodeOrError: PartitionHealthQuery_assetNodeOrError;
}

export interface PartitionHealthQueryVariables {
  assetKey: AssetKeyInput;
}
