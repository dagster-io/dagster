/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionHealthQuery
// ====================================================

export interface PartitionHealthQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface PartitionHealthQuery_assetNodes_materializationCountByPartition {
  __typename: "MaterializationCountByPartition";
  partition: string;
  materializationCount: number;
}

export interface PartitionHealthQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: PartitionHealthQuery_assetNodes_assetKey;
  materializationCountByPartition: PartitionHealthQuery_assetNodes_materializationCountByPartition[];
}

export interface PartitionHealthQuery {
  assetNodes: PartitionHealthQuery_assetNodes[];
}

export interface PartitionHealthQueryVariables {
  assetKeys: AssetKeyInput[];
}
