// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PreviousRunsForScheduleQuery
// ====================================================

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause | null;
}

export type PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats = PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results {
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
  tags: PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  stats: PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results_stats;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export type PreviousRunsForScheduleQuery_pipelineRunsOrError = PreviousRunsForScheduleQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PreviousRunsForScheduleQuery_pipelineRunsOrError_PipelineRuns;

export interface PreviousRunsForScheduleQuery {
  pipelineRunsOrError: PreviousRunsForScheduleQuery_pipelineRunsOrError;
}

export interface PreviousRunsForScheduleQueryVariables {
  filter?: PipelineRunsFilter | null;
  limit?: number | null;
}
