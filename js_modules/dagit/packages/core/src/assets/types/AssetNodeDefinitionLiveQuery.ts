/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetNodeDefinitionLiveQuery
// ====================================================

export interface AssetNodeDefinitionLiveQuery_assetsLatestInfo_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionLiveQuery_assetsLatestInfo_latestRun {
  __typename: "Run";
  status: RunStatus;
  id: string;
}

export interface AssetNodeDefinitionLiveQuery_assetsLatestInfo {
  __typename: "AssetLatestInfo";
  assetKey: AssetNodeDefinitionLiveQuery_assetsLatestInfo_assetKey;
  unstartedRunIds: string[];
  inProgressRunIds: string[];
  latestRun: AssetNodeDefinitionLiveQuery_assetsLatestInfo_latestRun | null;
}

export interface AssetNodeDefinitionLiveQuery {
  assetsLatestInfo: AssetNodeDefinitionLiveQuery_assetsLatestInfo[];
}

export interface AssetNodeDefinitionLiveQueryVariables {
  assetKeys: AssetKeyInput[];
}
