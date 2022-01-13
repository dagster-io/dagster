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

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_latestMaterializationByPartition_materializationEvent {
  __typename: "StepMaterializationEvent";
  timestamp: string;
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_latestMaterializationByPartition {
  __typename: "AssetMaterialization";
  partition: string | null;
  materializationEvent: PartitionHealthQuery_assetNodeOrError_AssetNode_latestMaterializationByPartition_materializationEvent;
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode {
  __typename: "AssetNode";
  id: string;
  partitionKeys: string[];
  latestMaterializationByPartition: PartitionHealthQuery_assetNodeOrError_AssetNode_latestMaterializationByPartition[];
}

export type PartitionHealthQuery_assetNodeOrError = PartitionHealthQuery_assetNodeOrError_AssetNotFoundError | PartitionHealthQuery_assetNodeOrError_AssetNode;

export interface PartitionHealthQuery {
  assetNodeOrError: PartitionHealthQuery_assetNodeOrError;
}

export interface PartitionHealthQueryVariables {
  assetKey: AssetKeyInput;
}
