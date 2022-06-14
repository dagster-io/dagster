/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetForNavigationQuery
// ====================================================

export interface AssetForNavigationQuery_materializedKeyOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetForNavigationQuery_materializedKeyOrError_MaterializedKey_definition_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetForNavigationQuery_materializedKeyOrError_MaterializedKey_definition_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetForNavigationQuery_materializedKeyOrError_MaterializedKey_definition_repository_location;
}

export interface AssetForNavigationQuery_materializedKeyOrError_MaterializedKey_definition {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  jobNames: string[];
  groupName: string | null;
  repository: AssetForNavigationQuery_materializedKeyOrError_MaterializedKey_definition_repository;
}

export interface AssetForNavigationQuery_materializedKeyOrError_MaterializedKey {
  __typename: "MaterializedKey";
  id: string;
  definition: AssetForNavigationQuery_materializedKeyOrError_MaterializedKey_definition | null;
}

export type AssetForNavigationQuery_materializedKeyOrError = AssetForNavigationQuery_materializedKeyOrError_AssetNotFoundError | AssetForNavigationQuery_materializedKeyOrError_MaterializedKey;

export interface AssetForNavigationQuery {
  materializedKeyOrError: AssetForNavigationQuery_materializedKeyOrError;
}

export interface AssetForNavigationQueryVariables {
  key: AssetKeyInput;
}
