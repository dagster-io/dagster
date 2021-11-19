/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LaunchedRunListQuery
// ====================================================

export interface LaunchedRunListQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause | null;
}

export type LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats = LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot | LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats_PythonError;

export interface LaunchedRunListQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  repositoryOrigin: LaunchedRunListQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  tags: LaunchedRunListQuery_pipelineRunsOrError_Runs_results_tags[];
  stats: LaunchedRunListQuery_pipelineRunsOrError_Runs_results_stats;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: LaunchedRunListQuery_pipelineRunsOrError_Runs_results[];
}

export interface LaunchedRunListQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchedRunListQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LaunchedRunListQuery_pipelineRunsOrError_PythonError_cause | null;
}

export type LaunchedRunListQuery_pipelineRunsOrError = LaunchedRunListQuery_pipelineRunsOrError_Runs | LaunchedRunListQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | LaunchedRunListQuery_pipelineRunsOrError_PythonError;

export interface LaunchedRunListQuery {
  pipelineRunsOrError: LaunchedRunListQuery_pipelineRunsOrError;
}

export interface LaunchedRunListQueryVariables {
  filter: RunsFilter;
}
