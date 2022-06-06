/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetTableDefinitionFragment
// ====================================================

export interface AssetTableDefinitionFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetTableDefinitionFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetTableDefinitionFragment_repository_location;
}

export interface AssetTableDefinitionFragment {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  partitionDefinition: string | null;
  description: string | null;
  repository: AssetTableDefinitionFragment_repository;
}
