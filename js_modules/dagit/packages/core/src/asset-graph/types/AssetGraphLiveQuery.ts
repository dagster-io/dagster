/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, AssetKeyInput, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphLiveQuery
// ====================================================

export interface AssetGraphLiveQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_inProgressRunsByStep_unstartedRuns {
  __typename: "Run";
  id: string;
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_inProgressRunsByStep_inProgressRuns {
  __typename: "Run";
  id: string;
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_inProgressRunsByStep {
  __typename: "InProgressRunsByStep";
  stepKey: string;
  unstartedRuns: AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_inProgressRunsByStep_unstartedRuns[];
  inProgressRuns: AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_inProgressRunsByStep_inProgressRuns[];
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_latestRunByStep_run {
  __typename: "Run";
  id: string;
  status: RunStatus;
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_latestRunByStep {
  __typename: "LatestRun";
  stepKey: string;
  run: AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_latestRunByStep_run | null;
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  inProgressRunsByStep: AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_inProgressRunsByStep[];
  latestRunByStep: AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes_latestRunByStep[];
}

export interface AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export type AssetGraphLiveQuery_repositoriesOrError = AssetGraphLiveQuery_repositoriesOrError_PythonError | AssetGraphLiveQuery_repositoriesOrError_RepositoryConnection;

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

export interface AssetGraphLiveQuery {
  repositoriesOrError: AssetGraphLiveQuery_repositoriesOrError;
  assetNodes: AssetGraphLiveQuery_assetNodes[];
}

export interface AssetGraphLiveQueryVariables {
  repositorySelector?: RepositorySelector | null;
  assetKeys?: AssetKeyInput[] | null;
}
