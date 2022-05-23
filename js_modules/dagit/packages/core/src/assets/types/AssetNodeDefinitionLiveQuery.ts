/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, AssetKeyInput, RunStatus } from "./../../types/globalTypes";

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
  latestRunByStep: AssetNodeDefinitionLiveQuery_repositoryOrError_Repository_latestRunByStep[];
}

export type AssetNodeDefinitionLiveQuery_repositoryOrError = AssetNodeDefinitionLiveQuery_repositoryOrError_PythonError | AssetNodeDefinitionLiveQuery_repositoryOrError_Repository;

export interface AssetNodeDefinitionLiveQuery_assetsLatestInfo_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionLiveQuery_assetsLatestInfo {
  __typename: "AssetLiveInfo";
  assetKey: AssetNodeDefinitionLiveQuery_assetsLatestInfo_assetKey;
  unstartedRunIds: string[];
  inProgressRunIds: string[];
}

export interface AssetNodeDefinitionLiveQuery {
  repositoryOrError: AssetNodeDefinitionLiveQuery_repositoryOrError;
  assetsLatestInfo: AssetNodeDefinitionLiveQuery_assetsLatestInfo[];
}

export interface AssetNodeDefinitionLiveQueryVariables {
  repositorySelector: RepositorySelector;
  assetKeys?: AssetKeyInput[] | null;
}
