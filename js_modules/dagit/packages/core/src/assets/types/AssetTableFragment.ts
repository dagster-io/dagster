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

export interface AssetTableFragment_definition_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetTableFragment_definition_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetTableFragment_definition_repository_location;
}

export interface AssetTableFragment_definition {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  partitionDefinition: string | null;
  description: string | null;
  repository: AssetTableFragment_definition_repository;
}

export interface AssetTableFragment {
  __typename: "MaterializedKey";
  id: string;
  key: AssetTableFragment_key;
  definition: AssetTableFragment_definition | null;
}
