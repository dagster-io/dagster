// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RepositoryInfoFragment
// ====================================================

export interface RepositoryInfoFragment_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositoryInfoFragment_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: RepositoryInfoFragment_origin_repositoryLocationMetadata[];
}

export interface RepositoryInfoFragment_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RepositoryInfoFragment {
  __typename: "Repository";
  id: string;
  name: string;
  origin: RepositoryInfoFragment_origin;
  location: RepositoryInfoFragment_location;
}
