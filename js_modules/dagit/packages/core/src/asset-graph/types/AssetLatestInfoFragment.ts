/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetLatestInfoFragment
// ====================================================

export interface AssetLatestInfoFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLatestInfoFragment_latestRun {
  __typename: "Run";
  id: string;
  status: RunStatus;
}

export interface AssetLatestInfoFragment {
  __typename: "AssetLatestInfo";
  assetKey: AssetLatestInfoFragment_assetKey;
  unstartedRunIds: string[];
  inProgressRunIds: string[];
  latestRun: AssetLatestInfoFragment_latestRun | null;
}
