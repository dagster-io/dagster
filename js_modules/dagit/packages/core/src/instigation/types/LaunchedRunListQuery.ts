// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LaunchedRunListQuery
// ====================================================

export interface LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause | null;
}

export type LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats = LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  tags: LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  stats: LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results_stats;
}

export interface LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns_results[];
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

export type LaunchedRunListQuery_pipelineRunsOrError = LaunchedRunListQuery_pipelineRunsOrError_PipelineRuns | LaunchedRunListQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | LaunchedRunListQuery_pipelineRunsOrError_PythonError;

export interface LaunchedRunListQuery {
  pipelineRunsOrError: LaunchedRunListQuery_pipelineRunsOrError;
}

export interface LaunchedRunListQueryVariables {
  filter: PipelineRunsFilter;
}
