/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LastRunQuery
// ====================================================

export interface LastRunQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface LastRunQuery_repositoryOrError_Repository_latestRunByStep_LatestRun_run {
  __typename: "Run";
  id: string;
  status: RunStatus;
}

export interface LastRunQuery_repositoryOrError_Repository_latestRunByStep_LatestRun {
  __typename: "LatestRun";
  stepKey: string;
  run: LastRunQuery_repositoryOrError_Repository_latestRunByStep_LatestRun_run | null;
}

export interface LastRunQuery_repositoryOrError_Repository_latestRunByStep_JobRunsCount {
  __typename: "JobRunsCount";
  stepKey: string;
  jobNames: string[];
  count: number;
  sinceLatestMaterialization: boolean;
}

export type LastRunQuery_repositoryOrError_Repository_latestRunByStep = LastRunQuery_repositoryOrError_Repository_latestRunByStep_LatestRun | LastRunQuery_repositoryOrError_Repository_latestRunByStep_JobRunsCount;

export interface LastRunQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  latestRunByStep: LastRunQuery_repositoryOrError_Repository_latestRunByStep[];
}

export type LastRunQuery_repositoryOrError = LastRunQuery_repositoryOrError_PythonError | LastRunQuery_repositoryOrError_Repository;

export interface LastRunQuery {
  repositoryOrError: LastRunQuery_repositoryOrError;
}

export interface LastRunQueryVariables {
  repositorySelector: RepositorySelector;
}
