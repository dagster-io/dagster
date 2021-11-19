/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PaginatedAssetKeysQuery
// ====================================================

export interface PaginatedAssetKeysQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface PaginatedAssetKeysQuery_assetsOrError_AssetConnection_nodes_definition {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobName: string | null;
  description: string | null;
}

export interface PaginatedAssetKeysQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  id: string;
  key: PaginatedAssetKeysQuery_assetsOrError_AssetConnection_nodes_key;
  definition: PaginatedAssetKeysQuery_assetsOrError_AssetConnection_nodes_definition | null;
}

export interface PaginatedAssetKeysQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: PaginatedAssetKeysQuery_assetsOrError_AssetConnection_nodes[];
}

export interface PaginatedAssetKeysQuery_assetsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PaginatedAssetKeysQuery_assetsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PaginatedAssetKeysQuery_assetsOrError_PythonError_cause | null;
}

export type PaginatedAssetKeysQuery_assetsOrError = PaginatedAssetKeysQuery_assetsOrError_AssetConnection | PaginatedAssetKeysQuery_assetsOrError_PythonError;

export interface PaginatedAssetKeysQuery {
  assetsOrError: PaginatedAssetKeysQuery_assetsOrError;
}

export interface PaginatedAssetKeysQueryVariables {
  prefix?: string[] | null;
  limit?: number | null;
  cursor?: string | null;
}
