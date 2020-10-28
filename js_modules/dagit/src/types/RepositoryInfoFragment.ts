// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RepositoryInfoFragment
// ====================================================

export interface RepositoryInfoFragment_origin_PythonRepositoryOrigin_repositoryMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositoryInfoFragment_origin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  executablePath: string;
  repositoryMetadata: RepositoryInfoFragment_origin_PythonRepositoryOrigin_repositoryMetadata[];
}

export interface RepositoryInfoFragment_origin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type RepositoryInfoFragment_origin = RepositoryInfoFragment_origin_PythonRepositoryOrigin | RepositoryInfoFragment_origin_GrpcRepositoryOrigin;

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
