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

export interface PartitionHealthQuery_assetNodeOrError_AssetNode_materializationCountByPartition {
  __typename: "MaterializationCountByPartition";
  partition: string;
  materializationCount: number;
}

export interface PartitionHealthQuery_assetNodeOrError_AssetNode {
  __typename: "AssetNode";
  id: string;
  materializationCountByPartition: PartitionHealthQuery_assetNodeOrError_AssetNode_materializationCountByPartition[];
}

export type PartitionHealthQuery_assetNodeOrError = PartitionHealthQuery_assetNodeOrError_AssetNotFoundError | PartitionHealthQuery_assetNodeOrError_AssetNode;

export interface PartitionHealthQuery {
  assetNodeOrError: PartitionHealthQuery_assetNodeOrError;
}

export interface PartitionHealthQueryVariables {
  assetKey: AssetKeyInput;
}
