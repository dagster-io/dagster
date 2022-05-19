/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RepositoryLiveFragment
// ====================================================

export interface RepositoryLiveFragment_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RepositoryLiveFragment_inProgressRunsByAsset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RepositoryLiveFragment_inProgressRunsByAsset_unstartedRuns {
  __typename: "Run";
  id: string;
}

export interface RepositoryLiveFragment_inProgressRunsByAsset_inProgressRuns {
  __typename: "Run";
  id: string;
}

export interface RepositoryLiveFragment_inProgressRunsByAsset {
  __typename: "InProgressRunsByAsset";
  assetKey: RepositoryLiveFragment_inProgressRunsByAsset_assetKey;
  unstartedRuns: RepositoryLiveFragment_inProgressRunsByAsset_unstartedRuns[];
  inProgressRuns: RepositoryLiveFragment_inProgressRunsByAsset_inProgressRuns[];
}

export interface RepositoryLiveFragment_latestRunByStep_run {
  __typename: "Run";
  id: string;
  status: RunStatus;
}

export interface RepositoryLiveFragment_latestRunByStep {
  __typename: "LatestRun";
  stepKey: string;
  run: RepositoryLiveFragment_latestRunByStep_run | null;
}

export interface RepositoryLiveFragment {
  __typename: "Repository";
  id: string;
  name: string;
  location: RepositoryLiveFragment_location;
  inProgressRunsByAsset: RepositoryLiveFragment_inProgressRunsByAsset[];
  latestRunByStep: RepositoryLiveFragment_latestRunByStep[];
}
