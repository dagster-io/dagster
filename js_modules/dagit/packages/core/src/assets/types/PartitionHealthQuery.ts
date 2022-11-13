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

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountGroupedByDimension {
  __typename: "MaterializationCountGroupedByDimension";
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountByPartition_partitionsCounts {
  __typename: "PartitionMaterializationCount";
  partition: string;
  materializationCount: number;
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountByPartition {
  __typename: "MaterializationCountByPartition";
  partitionsCounts: PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountByPartition_partitionsCounts[];
}

export type PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts = PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountGroupedByDimension | PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts_MaterializationCountByPartition;

export interface PartitionHealthQuery_assetNodeOrError_AssetNode {
  __typename: "AssetNode";
  id: string;
  partitionMaterializationCounts: PartitionHealthQuery_assetNodeOrError_AssetNode_partitionMaterializationCounts | null;
}

export type PartitionHealthQuery_assetNodeOrError = PartitionHealthQuery_assetNodeOrError_AssetNotFoundError | PartitionHealthQuery_assetNodeOrError_AssetNode;

export interface PartitionHealthQuery {
  assetNodeOrError: PartitionHealthQuery_assetNodeOrError;
}

export interface PartitionHealthQueryVariables {
  assetKey: AssetKeyInput;
}
