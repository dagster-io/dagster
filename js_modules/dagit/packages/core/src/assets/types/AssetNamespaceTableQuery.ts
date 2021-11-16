/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetNamespaceTableQuery
// ====================================================

export interface AssetNamespaceTableQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNamespaceTableQuery_assetsOrError_AssetConnection_nodes_definition {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobName: string | null;
  description: string | null;
}

export interface AssetNamespaceTableQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  id: string;
  key: AssetNamespaceTableQuery_assetsOrError_AssetConnection_nodes_key;
  definition: AssetNamespaceTableQuery_assetsOrError_AssetConnection_nodes_definition | null;
}

export interface AssetNamespaceTableQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: AssetNamespaceTableQuery_assetsOrError_AssetConnection_nodes[];
}

export interface AssetNamespaceTableQuery_assetsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AssetNamespaceTableQuery_assetsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AssetNamespaceTableQuery_assetsOrError_PythonError_cause | null;
}

export type AssetNamespaceTableQuery_assetsOrError = AssetNamespaceTableQuery_assetsOrError_AssetConnection | AssetNamespaceTableQuery_assetsOrError_PythonError;

export interface AssetNamespaceTableQuery {
  assetsOrError: AssetNamespaceTableQuery_assetsOrError;
}

export interface AssetNamespaceTableQueryVariables {
  prefix?: string[] | null;
}
