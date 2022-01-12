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

export interface AssetTableFragment_definition_jobs_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetTableFragment_definition_jobs_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetTableFragment_definition_jobs_repository_location;
}

export interface AssetTableFragment_definition_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
  repository: AssetTableFragment_definition_jobs_repository;
}

export interface AssetTableFragment_definition {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  jobs: AssetTableFragment_definition_jobs[];
}

export interface AssetTableFragment {
  __typename: "Asset";
  id: string;
  key: AssetTableFragment_key;
  definition: AssetTableFragment_definition | null;
}
