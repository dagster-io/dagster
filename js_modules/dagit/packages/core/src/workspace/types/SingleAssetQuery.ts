/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, RunStatus } from "./../../types/globalTypes";

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

export interface SingleAssetQuery_assetOrError_Asset_definition_partitionDefinition {
  __typename: "PartitionDefinition";
  description: string;
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

export interface SingleAssetQuery_assetOrError_Asset_definition_freshnessPolicy {
  __typename: "FreshnessPolicy";
  maximumLagMinutes: number;
  cronSchedule: string | null;
}

export interface SingleAssetQuery_assetOrError_Asset_definition_freshnessInfo {
  __typename: "AssetFreshnessInfo";
  currentMinutesLate: number | null;
}

export interface SingleAssetQuery_assetOrError_Asset_definition_assetObservations {
  __typename: "ObservationEvent";
  timestamp: string;
  runId: string;
}

export interface SingleAssetQuery_assetOrError_Asset_definition {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  isSource: boolean;
  partitionDefinition: SingleAssetQuery_assetOrError_Asset_definition_partitionDefinition | null;
  description: string | null;
  repository: SingleAssetQuery_assetOrError_Asset_definition_repository;
  opNames: string[];
  assetKey: SingleAssetQuery_assetOrError_Asset_definition_assetKey;
  assetMaterializations: SingleAssetQuery_assetOrError_Asset_definition_assetMaterializations[];
  freshnessPolicy: SingleAssetQuery_assetOrError_Asset_definition_freshnessPolicy | null;
  freshnessInfo: SingleAssetQuery_assetOrError_Asset_definition_freshnessInfo | null;
  assetObservations: SingleAssetQuery_assetOrError_Asset_definition_assetObservations[];
  currentLogicalVersion: string | null;
  projectedLogicalVersion: string | null;
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
  id: string;
  status: RunStatus;
}

export interface SingleAssetQuery_assetsLatestInfo {
  __typename: "AssetLatestInfo";
  assetKey: SingleAssetQuery_assetsLatestInfo_assetKey;
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
