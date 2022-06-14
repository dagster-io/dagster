/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetsCatalogRootQuery
// ====================================================

export interface AssetsCatalogRootQuery_materializedKeyOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetsCatalogRootQuery_materializedKeyOrError_MaterializedKey_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetsCatalogRootQuery_materializedKeyOrError_MaterializedKey {
  __typename: "MaterializedKey";
  id: string;
  key: AssetsCatalogRootQuery_materializedKeyOrError_MaterializedKey_key;
}

export type AssetsCatalogRootQuery_materializedKeyOrError = AssetsCatalogRootQuery_materializedKeyOrError_AssetNotFoundError | AssetsCatalogRootQuery_materializedKeyOrError_MaterializedKey;

export interface AssetsCatalogRootQuery {
  materializedKeyOrError: AssetsCatalogRootQuery_materializedKeyOrError;
}

export interface AssetsCatalogRootQueryVariables {
  assetKey: AssetKeyInput;
}
