// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AssetWipeMutation
// ====================================================

export interface AssetWipeMutation_wipeAsset_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetWipeMutation_wipeAsset_AssetWipeSuccess_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetWipeMutation_wipeAsset_AssetWipeSuccess {
  __typename: "AssetWipeSuccess";
  assetKey: AssetWipeMutation_wipeAsset_AssetWipeSuccess_assetKey;
}

export interface AssetWipeMutation_wipeAsset_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type AssetWipeMutation_wipeAsset = AssetWipeMutation_wipeAsset_AssetNotFoundError | AssetWipeMutation_wipeAsset_AssetWipeSuccess | AssetWipeMutation_wipeAsset_PythonError;

export interface AssetWipeMutation {
  wipeAsset: AssetWipeMutation_wipeAsset;
}

export interface AssetWipeMutationVariables {
  assetKey: AssetKeyInput;
}
