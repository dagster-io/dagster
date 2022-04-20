/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: OmittedAssetCountQuery
// ====================================================

export interface OmittedAssetCountQuery_assetsOrError_PythonError {
  __typename: "PythonError";
}

export interface OmittedAssetCountQuery_assetsOrError_AssetConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface OmittedAssetCountQuery_assetsOrError_AssetConnection_nodes {
  __typename: "Asset";
  id: string;
  key: OmittedAssetCountQuery_assetsOrError_AssetConnection_nodes_key;
}

export interface OmittedAssetCountQuery_assetsOrError_AssetConnection {
  __typename: "AssetConnection";
  nodes: OmittedAssetCountQuery_assetsOrError_AssetConnection_nodes[];
}

export type OmittedAssetCountQuery_assetsOrError = OmittedAssetCountQuery_assetsOrError_PythonError | OmittedAssetCountQuery_assetsOrError_AssetConnection;

export interface OmittedAssetCountQuery {
  assetsOrError: OmittedAssetCountQuery_assetsOrError;
}
