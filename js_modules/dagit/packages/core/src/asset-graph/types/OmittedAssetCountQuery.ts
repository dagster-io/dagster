/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: OmittedAssetCountQuery
// ====================================================

export interface OmittedAssetCountQuery_materializedKeysOrError_PythonError {
  __typename: "PythonError";
}

export interface OmittedAssetCountQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_key {
  __typename: "AssetKey";
  path: string[];
}

export interface OmittedAssetCountQuery_materializedKeysOrError_MaterializedKeysConnection_nodes {
  __typename: "MaterializedKey";
  id: string;
  key: OmittedAssetCountQuery_materializedKeysOrError_MaterializedKeysConnection_nodes_key;
}

export interface OmittedAssetCountQuery_materializedKeysOrError_MaterializedKeysConnection {
  __typename: "MaterializedKeysConnection";
  nodes: OmittedAssetCountQuery_materializedKeysOrError_MaterializedKeysConnection_nodes[];
}

export type OmittedAssetCountQuery_materializedKeysOrError = OmittedAssetCountQuery_materializedKeysOrError_PythonError | OmittedAssetCountQuery_materializedKeysOrError_MaterializedKeysConnection;

export interface OmittedAssetCountQuery {
  materializedKeysOrError: OmittedAssetCountQuery_materializedKeysOrError;
}
