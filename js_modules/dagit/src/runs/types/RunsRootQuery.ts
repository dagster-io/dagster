// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunsRootQuery
// ====================================================

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause | null;
}

export type RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats = RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results {
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
  tags: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  stats: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats;
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export interface RunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface RunsRootQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type RunsRootQuery_pipelineRunsOrError = RunsRootQuery_pipelineRunsOrError_PipelineRuns | RunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | RunsRootQuery_pipelineRunsOrError_PythonError;

export interface RunsRootQuery_queuedCount_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface RunsRootQuery_queuedCount_PipelineRuns {
  __typename: "PipelineRuns";
  count: number | null;
}

export type RunsRootQuery_queuedCount = RunsRootQuery_queuedCount_InvalidPipelineRunsFilterError | RunsRootQuery_queuedCount_PipelineRuns;

export interface RunsRootQuery_inProgressCount_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface RunsRootQuery_inProgressCount_PipelineRuns {
  __typename: "PipelineRuns";
  count: number | null;
}

export type RunsRootQuery_inProgressCount = RunsRootQuery_inProgressCount_InvalidPipelineRunsFilterError | RunsRootQuery_inProgressCount_PipelineRuns;

export interface RunsRootQuery {
  pipelineRunsOrError: RunsRootQuery_pipelineRunsOrError;
  queuedCount: RunsRootQuery_queuedCount;
  inProgressCount: RunsRootQuery_inProgressCount;
}

export interface RunsRootQueryVariables {
  limit?: number | null;
  cursor?: string | null;
  filter: PipelineRunsFilter;
  queuedFilter: PipelineRunsFilter;
  inProgressFilter: PipelineRunsFilter;
}
