/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetIdScanQuery
// ====================================================

export interface AssetIdScanQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
}

export interface AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes_assetNodes {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  assetKey: AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes_assetNodes_assetKey;
}

export interface AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  assetNodes: AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes_assetNodes[];
}

export interface AssetIdScanQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export type AssetIdScanQuery_repositoriesOrError = AssetIdScanQuery_repositoriesOrError_PythonError | AssetIdScanQuery_repositoriesOrError_RepositoryConnection;

export interface AssetIdScanQuery {
  repositoriesOrError: AssetIdScanQuery_repositoriesOrError;
}
