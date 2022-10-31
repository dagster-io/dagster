/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetCatalogTableQuery
// ====================================================

export interface AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_definition_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_definition_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_definition_repository_location;
}

export interface AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_definition {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  partitionDefinition: string | null;
  description: string | null;
  repository: AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_definition_repository;
}

export interface AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  id: string;
  key: AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_key;
  definition: AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes_definition | null;
}

export interface AssetCatalogTableQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes[];
}

export interface AssetCatalogTableQuery_assetsOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AssetCatalogTableQuery_assetsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: AssetCatalogTableQuery_assetsOrError_PythonError_causes[];
}

export type AssetCatalogTableQuery_assetsOrError = AssetCatalogTableQuery_assetsOrError_AssetConnection | AssetCatalogTableQuery_assetsOrError_PythonError;

export interface AssetCatalogTableQuery {
  assetsOrError: AssetCatalogTableQuery_assetsOrError;
}
