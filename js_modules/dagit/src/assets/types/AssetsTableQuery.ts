// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetsTableQuery
// ====================================================

export interface AssetsTableQuery_assetsOrError_AssetsNotSupportedError {
  __typename: "AssetsNotSupportedError";
  message: string;
}

export interface AssetsTableQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetsTableQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  key: AssetsTableQuery_assetsOrError_AssetConnection_nodes_key;
}

export interface AssetsTableQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: AssetsTableQuery_assetsOrError_AssetConnection_nodes[];
}

export type AssetsTableQuery_assetsOrError = AssetsTableQuery_assetsOrError_AssetsNotSupportedError | AssetsTableQuery_assetsOrError_AssetConnection;

export interface AssetsTableQuery {
  assetsOrError: AssetsTableQuery_assetsOrError;
}

export interface AssetsTableQueryVariables {
  prefixPath?: string[] | null;
}
