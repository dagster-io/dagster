// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunsRootQuery
// ====================================================

export interface PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause | null;
}

export type PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats = PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results {
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
  tags: PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  stats: PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type PipelineRunsRootQuery_pipelineRunsOrError = PipelineRunsRootQuery_pipelineRunsOrError_PipelineRuns | PipelineRunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PipelineRunsRootQuery_pipelineRunsOrError_PythonError;

export interface PipelineRunsRootQuery {
  pipelineRunsOrError: PipelineRunsRootQuery_pipelineRunsOrError;
}

export interface PipelineRunsRootQueryVariables {
  limit?: number | null;
  cursor?: string | null;
  filter: PipelineRunsFilter;
}
