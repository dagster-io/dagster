// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetEntryRootQuery
// ====================================================

export interface AssetEntryRootQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetEntryRootQuery_assetOrError_AssetsNotSupportedError {
  __typename: "AssetsNotSupportedError";
  message: string;
}

export interface AssetEntryRootQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEntryRootQuery_assetOrError_Asset {
  __typename: "Asset";
  key: AssetEntryRootQuery_assetOrError_Asset_key;
}

export type AssetEntryRootQuery_assetOrError = AssetEntryRootQuery_assetOrError_AssetNotFoundError | AssetEntryRootQuery_assetOrError_AssetsNotSupportedError | AssetEntryRootQuery_assetOrError_Asset;

export interface AssetEntryRootQuery {
  assetOrError: AssetEntryRootQuery_assetOrError;
}

export interface AssetEntryRootQueryVariables {
  assetKey: AssetKeyInput;
}
