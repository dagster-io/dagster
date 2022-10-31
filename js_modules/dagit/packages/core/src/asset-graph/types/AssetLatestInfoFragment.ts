/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetComputeStatus, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetLatestInfoFragment
// ====================================================

export interface AssetLatestInfoFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLatestInfoFragment_latestRun {
  __typename: "Run";
  status: RunStatus;
  id: string;
}

export interface AssetLatestInfoFragment {
  __typename: "AssetLatestInfo";
  assetKey: AssetLatestInfoFragment_assetKey;
  computeStatus: AssetComputeStatus;
  unstartedRunIds: string[];
  inProgressRunIds: string[];
  latestRun: AssetLatestInfoFragment_latestRun | null;
}
