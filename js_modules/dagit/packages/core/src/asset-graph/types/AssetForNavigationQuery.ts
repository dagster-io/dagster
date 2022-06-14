/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetForNavigationQuery
// ====================================================

export interface AssetForNavigationQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetForNavigationQuery_assetOrError_Asset_definition_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetForNavigationQuery_assetOrError_Asset_definition_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetForNavigationQuery_assetOrError_Asset_definition_repository_location;
}

export interface AssetForNavigationQuery_assetOrError_Asset_definition {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  jobNames: string[];
  groupName: string | null;
  repository: AssetForNavigationQuery_assetOrError_Asset_definition_repository;
}

export interface AssetForNavigationQuery_assetOrError_Asset {
  __typename: "Asset";
  id: string;
  definition: AssetForNavigationQuery_assetOrError_Asset_definition | null;
}

export type AssetForNavigationQuery_assetOrError = AssetForNavigationQuery_assetOrError_AssetNotFoundError | AssetForNavigationQuery_assetOrError_Asset;

export interface AssetForNavigationQuery {
  assetOrError: AssetForNavigationQuery_assetOrError;
}

export interface AssetForNavigationQueryVariables {
  key: AssetKeyInput;
}
