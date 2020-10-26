// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RepositoryInfoFragment
// ====================================================

export interface RepositoryInfoFragment_origin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface RepositoryInfoFragment_origin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: RepositoryInfoFragment_origin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface RepositoryInfoFragment_origin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: RepositoryInfoFragment_origin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface RepositoryInfoFragment_origin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type RepositoryInfoFragment_origin = RepositoryInfoFragment_origin_PythonRepositoryOrigin | RepositoryInfoFragment_origin_GrpcRepositoryOrigin;

export interface RepositoryInfoFragment_location {
  __typename: "RepositoryLocation";
  name: string;
}

export interface RepositoryInfoFragment {
  __typename: "Repository";
  name: string;
  origin: RepositoryInfoFragment_origin;
  location: RepositoryInfoFragment_location;
}
