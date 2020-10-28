// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RepositoryOriginFragment
// ====================================================

export interface RepositoryOriginFragment_PythonRepositoryOrigin_repositoryMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositoryOriginFragment_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  executablePath: string;
  repositoryMetadata: RepositoryOriginFragment_PythonRepositoryOrigin_repositoryMetadata[];
}

export interface RepositoryOriginFragment_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type RepositoryOriginFragment = RepositoryOriginFragment_PythonRepositoryOrigin | RepositoryOriginFragment_GrpcRepositoryOrigin;
