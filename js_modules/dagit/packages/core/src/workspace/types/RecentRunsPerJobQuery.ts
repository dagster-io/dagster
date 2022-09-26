/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RecentRunsPerJobQuery
// ====================================================

export interface RecentRunsPerJobQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface RecentRunsPerJobQuery_repositoryOrError_Repository_pipelines_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface RecentRunsPerJobQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  runs: RecentRunsPerJobQuery_repositoryOrError_Repository_pipelines_runs[];
}

export interface RecentRunsPerJobQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RecentRunsPerJobQuery_repositoryOrError_Repository_pipelines[];
}

export interface RecentRunsPerJobQuery_repositoryOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RecentRunsPerJobQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RecentRunsPerJobQuery_repositoryOrError_PythonError_causes[];
}

export type RecentRunsPerJobQuery_repositoryOrError = RecentRunsPerJobQuery_repositoryOrError_RepositoryNotFoundError | RecentRunsPerJobQuery_repositoryOrError_Repository | RecentRunsPerJobQuery_repositoryOrError_PythonError;

export interface RecentRunsPerJobQuery {
  repositoryOrError: RecentRunsPerJobQuery_repositoryOrError;
}

export interface RecentRunsPerJobQueryVariables {
  selector: RepositorySelector;
}
