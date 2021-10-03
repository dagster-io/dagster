// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetsTableMaterializationsQuery
// ====================================================

export interface AssetsTableMaterializationsQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetsTableMaterializationsQuery_assetsOrError_AssetConnection_nodes_tags {
  __typename: "AssetTag";
  key: string;
  value: string;
}

export interface AssetsTableMaterializationsQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  id: string;
  key: AssetsTableMaterializationsQuery_assetsOrError_AssetConnection_nodes_key;
  tags: AssetsTableMaterializationsQuery_assetsOrError_AssetConnection_nodes_tags[];
}

export interface AssetsTableMaterializationsQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: AssetsTableMaterializationsQuery_assetsOrError_AssetConnection_nodes[];
}

export interface AssetsTableMaterializationsQuery_assetsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AssetsTableMaterializationsQuery_assetsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AssetsTableMaterializationsQuery_assetsOrError_PythonError_cause | null;
}

export type AssetsTableMaterializationsQuery_assetsOrError = AssetsTableMaterializationsQuery_assetsOrError_AssetConnection | AssetsTableMaterializationsQuery_assetsOrError_PythonError;

export interface AssetsTableMaterializationsQuery {
  assetsOrError: AssetsTableMaterializationsQuery_assetsOrError;
}
