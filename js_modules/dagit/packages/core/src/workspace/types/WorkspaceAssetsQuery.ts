/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: WorkspaceAssetsQuery
// ====================================================

export interface WorkspaceAssetsQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface WorkspaceAssetsQuery_repositoryOrError_Repository_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface WorkspaceAssetsQuery_repositoryOrError_Repository_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: WorkspaceAssetsQuery_repositoryOrError_Repository_assetNodes_assetKey;
  groupName: string | null;
}

export interface WorkspaceAssetsQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  assetNodes: WorkspaceAssetsQuery_repositoryOrError_Repository_assetNodes[];
}

export interface WorkspaceAssetsQuery_repositoryOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceAssetsQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceAssetsQuery_repositoryOrError_PythonError_causes[];
}

export type WorkspaceAssetsQuery_repositoryOrError = WorkspaceAssetsQuery_repositoryOrError_RepositoryNotFoundError | WorkspaceAssetsQuery_repositoryOrError_Repository | WorkspaceAssetsQuery_repositoryOrError_PythonError;

export interface WorkspaceAssetsQuery {
  repositoryOrError: WorkspaceAssetsQuery_repositoryOrError;
}

export interface WorkspaceAssetsQueryVariables {
  selector: RepositorySelector;
}
