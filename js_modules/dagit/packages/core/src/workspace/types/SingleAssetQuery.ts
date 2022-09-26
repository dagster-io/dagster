/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, AssetComputeStatus, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SingleAssetQuery
// ====================================================

export interface SingleAssetQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface SingleAssetQuery_assetOrError_Asset_assetMaterializations {
  __typename: "MaterializationEvent";
  runId: string;
  timestamp: string;
}

export interface SingleAssetQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface SingleAssetQuery_assetOrError_Asset_definition_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface SingleAssetQuery_assetOrError_Asset_definition_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: SingleAssetQuery_assetOrError_Asset_definition_repository_location;
}

export interface SingleAssetQuery_assetOrError_Asset_definition_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SingleAssetQuery_assetOrError_Asset_definition_assetMaterializations {
  __typename: "MaterializationEvent";
  timestamp: string;
  runId: string;
}

export interface SingleAssetQuery_assetOrError_Asset_definition {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  partitionDefinition: string | null;
  description: string | null;
  repository: SingleAssetQuery_assetOrError_Asset_definition_repository;
  opNames: string[];
  assetKey: SingleAssetQuery_assetOrError_Asset_definition_assetKey;
  assetMaterializations: SingleAssetQuery_assetOrError_Asset_definition_assetMaterializations[];
}

export interface SingleAssetQuery_assetOrError_Asset {
  __typename: "Asset";
  id: string;
  assetMaterializations: SingleAssetQuery_assetOrError_Asset_assetMaterializations[];
  key: SingleAssetQuery_assetOrError_Asset_key;
  definition: SingleAssetQuery_assetOrError_Asset_definition | null;
}

export type SingleAssetQuery_assetOrError = SingleAssetQuery_assetOrError_AssetNotFoundError | SingleAssetQuery_assetOrError_Asset;

export interface SingleAssetQuery_assetsLatestInfo_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SingleAssetQuery_assetsLatestInfo_latestRun {
  __typename: "Run";
  status: RunStatus;
  id: string;
}

export interface SingleAssetQuery_assetsLatestInfo {
  __typename: "AssetLatestInfo";
  assetKey: SingleAssetQuery_assetsLatestInfo_assetKey;
  computeStatus: AssetComputeStatus;
  unstartedRunIds: string[];
  inProgressRunIds: string[];
  latestRun: SingleAssetQuery_assetsLatestInfo_latestRun | null;
}

export interface SingleAssetQuery {
  assetOrError: SingleAssetQuery_assetOrError;
  assetsLatestInfo: SingleAssetQuery_assetsLatestInfo[];
}

export interface SingleAssetQueryVariables {
  input: AssetKeyInput;
}
