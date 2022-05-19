/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetNodeDefinitionLiveQuery
// ====================================================

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset_unstartedRuns {
  __typename: "Run";
  id: string;
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset_inProgressRuns {
  __typename: "Run";
  id: string;
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset {
  __typename: "InProgressRunsByAsset";
  assetKey: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset_assetKey;
  unstartedRuns: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset_unstartedRuns[];
  inProgressRuns: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset_inProgressRuns[];
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_latestRunByStep_run {
  __typename: "Run";
  id: string;
  status: RunStatus;
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_latestRunByStep {
  __typename: "LatestRun";
  stepKey: string;
  run: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_latestRunByStep_run | null;
}

export interface AssetNodeDefinitionLiveQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_location;
  inProgressRunsByAsset: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_inProgressRunsByAsset[];
  latestRunByStep: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_latestRunByStep[];
}

export type AssetNodeDefinitionLiveQuery_repositoryOrError = AssetNodeDefinitionLiveQuery_repositoryOrError_PythonError | AssetNodeDefinitionLiveQuery_repositoryOrError_Repository;

export interface AssetNodeDefinitionLiveQuery {
  repositoryOrError: AssetNodeDefinitionLiveQuery_repositoryOrError;
}

export interface AssetNodeDefinitionLiveQueryVariables {
  repositorySelector: RepositorySelector;
}
