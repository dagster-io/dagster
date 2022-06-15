/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetTableFragment
// ====================================================

export interface AssetTableFragment_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetTableFragment_assetNode_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetTableFragment_assetNode_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetTableFragment_assetNode_repository_location;
}

export interface AssetTableFragment_assetNode {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  partitionDefinition: string | null;
  description: string | null;
  repository: AssetTableFragment_assetNode_repository;
}

export interface AssetTableFragment {
  __typename: "MaterializedKey";
  id: string;
  key: AssetTableFragment_key;
  assetNode: AssetTableFragment_assetNode | null;
}
