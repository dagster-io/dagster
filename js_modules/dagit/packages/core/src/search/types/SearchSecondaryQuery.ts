/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchSecondaryQuery
// ====================================================

export interface SearchSecondaryQuery_materializedKeysOrError_PythonError {
  __typename: "PythonError";
}

export interface SearchSecondaryQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface SearchSecondaryQuery_materializedKeysOrError_MaterializedKeysConnection_nodes {
  __typename: "MaterializedKey";
  id: string;
  key: SearchSecondaryQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_key;
}

export interface SearchSecondaryQuery_materializedKeysOrError_MaterializedKeysConnection {
  __typename: "MaterializedKeysConnection";
  nodes: SearchSecondaryQuery_materializedKeysOrError_MaterializedKeysConnection_nodes[];
}

export type SearchSecondaryQuery_materializedKeysOrError = SearchSecondaryQuery_materializedKeysOrError_PythonError | SearchSecondaryQuery_materializedKeysOrError_MaterializedKeysConnection;

export interface SearchSecondaryQuery {
  materializedKeysOrError: SearchSecondaryQuery_materializedKeysOrError;
}
