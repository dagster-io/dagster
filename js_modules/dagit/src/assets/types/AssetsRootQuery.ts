// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AssetsRootQuery
// ====================================================

export interface AssetsRootQuery_assetsOrError_AssetsNotSupportedError {
  __typename: "AssetsNotSupportedError";
  message: string;
}

export interface AssetsRootQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetsRootQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  key: AssetsRootQuery_assetsOrError_AssetConnection_nodes_key;
}

export interface AssetsRootQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: AssetsRootQuery_assetsOrError_AssetConnection_nodes[];
}

export type AssetsRootQuery_assetsOrError = AssetsRootQuery_assetsOrError_AssetsNotSupportedError | AssetsRootQuery_assetsOrError_AssetConnection;

export interface AssetsRootQuery {
  assetsOrError: AssetsRootQuery_assetsOrError;
}
