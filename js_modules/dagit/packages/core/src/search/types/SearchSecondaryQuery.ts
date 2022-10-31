/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchSecondaryQuery
// ====================================================

export interface SearchSecondaryQuery_assetsOrError_PythonError {
  __typename: "PythonError";
}

export interface SearchSecondaryQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface SearchSecondaryQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  id: string;
  key: SearchSecondaryQuery_assetsOrError_AssetConnection_nodes_key;
}

export interface SearchSecondaryQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: SearchSecondaryQuery_assetsOrError_AssetConnection_nodes[];
}

export type SearchSecondaryQuery_assetsOrError = SearchSecondaryQuery_assetsOrError_PythonError | SearchSecondaryQuery_assetsOrError_AssetConnection;

export interface SearchSecondaryQuery {
  assetsOrError: SearchSecondaryQuery_assetsOrError;
}
