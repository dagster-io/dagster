// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RepositoryOriginFragment
// ====================================================

export interface RepositoryOriginFragment_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface RepositoryOriginFragment_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: RepositoryOriginFragment_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface RepositoryOriginFragment_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: RepositoryOriginFragment_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface RepositoryOriginFragment_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type RepositoryOriginFragment = RepositoryOriginFragment_PythonRepositoryOrigin | RepositoryOriginFragment_GrpcRepositoryOrigin;
