/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeFragment
// ====================================================

export interface AssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeFragment_repository_location;
}

export interface AssetNodeFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  partitionDefinition: string | null;
  assetKey: AssetNodeFragment_assetKey;
  repository: AssetNodeFragment_repository;
}
