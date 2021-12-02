/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetNodeDefinitionRunsQuery
// ====================================================

export interface AssetNodeDefinitionRunsQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface AssetNodeDefinitionRunsQuery_repositoryOrError_Repository_inProgressRunsByStep_runs {
  __typename: "Run";
  id: string;
  runId: string;
}

export interface AssetNodeDefinitionRunsQuery_repositoryOrError_Repository_inProgressRunsByStep {
  __typename: "InProgressRunsByStep";
  stepKey: string;
  runs: AssetNodeDefinitionRunsQuery_repositoryOrError_Repository_inProgressRunsByStep_runs[];
}

export interface AssetNodeDefinitionRunsQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  inProgressRunsByStep: AssetNodeDefinitionRunsQuery_repositoryOrError_Repository_inProgressRunsByStep[];
}

export type AssetNodeDefinitionRunsQuery_repositoryOrError = AssetNodeDefinitionRunsQuery_repositoryOrError_PythonError | AssetNodeDefinitionRunsQuery_repositoryOrError_Repository;

export interface AssetNodeDefinitionRunsQuery {
  repositoryOrError: AssetNodeDefinitionRunsQuery_repositoryOrError;
}

export interface AssetNodeDefinitionRunsQueryVariables {
  repositorySelector: RepositorySelector;
}
