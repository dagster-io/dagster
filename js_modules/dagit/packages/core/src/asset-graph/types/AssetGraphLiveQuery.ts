/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, AssetComputeStatus, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphLiveQuery
// ====================================================

export interface AssetGraphLiveQuery_assetNodes_repository {
  __typename: "Repository";
  id: string;
}

export interface AssetGraphLiveQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphLiveQuery_assetNodes_assetMaterializations {
  __typename: "MaterializationEvent";
  timestamp: string;
  runId: string;
}

export interface AssetGraphLiveQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  repository: AssetGraphLiveQuery_assetNodes_repository;
  assetKey: AssetGraphLiveQuery_assetNodes_assetKey;
  assetMaterializations: AssetGraphLiveQuery_assetNodes_assetMaterializations[];
}

export interface AssetGraphLiveQuery_assetsLatestInfo_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphLiveQuery_assetsLatestInfo_latestRun {
  __typename: "Run";
  status: RunStatus;
  id: string;
}

export interface AssetGraphLiveQuery_assetsLatestInfo {
  __typename: "AssetLatestInfo";
  assetKey: AssetGraphLiveQuery_assetsLatestInfo_assetKey;
  computeStatus: AssetComputeStatus;
  unstartedRunIds: string[];
  inProgressRunIds: string[];
  latestRun: AssetGraphLiveQuery_assetsLatestInfo_latestRun | null;
}

export interface AssetGraphLiveQuery {
  assetNodes: AssetGraphLiveQuery_assetNodes[];
  assetsLatestInfo: AssetGraphLiveQuery_assetsLatestInfo[];
}

export interface AssetGraphLiveQueryVariables {
  assetKeys: AssetKeyInput[];
}
