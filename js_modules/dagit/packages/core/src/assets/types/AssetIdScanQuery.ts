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
  name: string;
}

export interface AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes_assetNodes {
  __typename: "AssetNode";
  id: string;
}

export interface AssetIdScanQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
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
