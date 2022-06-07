/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetsCatalogRootQuery
// ====================================================

export interface AssetsCatalogRootQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetsCatalogRootQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetsCatalogRootQuery_assetOrError_Asset {
  __typename: "Asset";
  id: string;
  key: AssetsCatalogRootQuery_assetOrError_Asset_key;
}

export type AssetsCatalogRootQuery_assetOrError = AssetsCatalogRootQuery_assetOrError_AssetNotFoundError | AssetsCatalogRootQuery_assetOrError_Asset;

export interface AssetsCatalogRootQuery {
  assetOrError: AssetsCatalogRootQuery_assetOrError;
}

export interface AssetsCatalogRootQueryVariables {
  assetKey: AssetKeyInput;
}
