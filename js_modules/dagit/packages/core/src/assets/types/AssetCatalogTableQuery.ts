/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetCatalogTableQuery
// ====================================================

export interface AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_definition_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_definition_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_definition_repository_location;
}

export interface AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_definition {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  partitionDefinition: string | null;
  description: string | null;
  repository: AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_definition_repository;
}

export interface AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes {
  __typename: "MaterializedKey";
  id: string;
  key: AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_key;
  definition: AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_definition | null;
}

export interface AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection {
  __typename: "MaterializedKeysConnection";
  nodes: AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection_nodes[];
}

export interface AssetCatalogTableQuery_materializedKeysOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AssetCatalogTableQuery_materializedKeysOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AssetCatalogTableQuery_materializedKeysOrError_PythonError_cause | null;
}

export type AssetCatalogTableQuery_materializedKeysOrError = AssetCatalogTableQuery_materializedKeysOrError_MaterializedKeysConnection | AssetCatalogTableQuery_materializedKeysOrError_PythonError;

export interface AssetCatalogTableQuery {
  materializedKeysOrError: AssetCatalogTableQuery_materializedKeysOrError;
}
