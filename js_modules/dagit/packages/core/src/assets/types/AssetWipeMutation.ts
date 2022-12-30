/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AssetWipeMutation
// ====================================================

export interface AssetWipeMutation_wipeAssets_AssetNotFoundError {
  __typename: "AssetNotFoundError" | "UnauthorizedError";
}

export interface AssetWipeMutation_wipeAssets_AssetWipeSuccess_assetKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetWipeMutation_wipeAssets_AssetWipeSuccess {
  __typename: "AssetWipeSuccess";
  assetKeys: AssetWipeMutation_wipeAssets_AssetWipeSuccess_assetKeys[];
}

export interface AssetWipeMutation_wipeAssets_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AssetWipeMutation_wipeAssets_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: AssetWipeMutation_wipeAssets_PythonError_causes[];
}

export type AssetWipeMutation_wipeAssets = AssetWipeMutation_wipeAssets_AssetNotFoundError | AssetWipeMutation_wipeAssets_AssetWipeSuccess | AssetWipeMutation_wipeAssets_PythonError;

export interface AssetWipeMutation {
  wipeAssets: AssetWipeMutation_wipeAssets;
}

export interface AssetWipeMutationVariables {
  assetKeys: AssetKeyInput[];
}
