/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RepositoryInfoFragment
// ====================================================

export interface RepositoryInfoFragment_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RepositoryInfoFragment_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositoryInfoFragment {
  __typename: "Repository";
  id: string;
  name: string;
  location: RepositoryInfoFragment_location;
  displayMetadata: RepositoryInfoFragment_displayMetadata[];
}
