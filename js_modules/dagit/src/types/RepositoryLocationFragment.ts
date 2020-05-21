// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RepositoryLocationFragment
// ====================================================

export interface RepositoryLocationFragment_repositories_pipelines {
  __typename: "Pipeline";
  name: string;
}

export interface RepositoryLocationFragment_repositories {
  __typename: "Repository";
  name: string;
  pipelines: RepositoryLocationFragment_repositories_pipelines[];
}

export interface RepositoryLocationFragment {
  __typename: "RepositoryLocation";
  name: string;
  repositories: RepositoryLocationFragment_repositories[];
}
