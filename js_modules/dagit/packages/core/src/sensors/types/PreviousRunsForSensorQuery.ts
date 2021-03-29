// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PreviousRunsForSensorQuery
// ====================================================

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause | null;
}

export type PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats = PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results {
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
  tags: PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  stats: PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results_stats;
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export type PreviousRunsForSensorQuery_pipelineRunsOrError = PreviousRunsForSensorQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PreviousRunsForSensorQuery_pipelineRunsOrError_PipelineRuns;

export interface PreviousRunsForSensorQuery {
  pipelineRunsOrError: PreviousRunsForSensorQuery_pipelineRunsOrError;
}

export interface PreviousRunsForSensorQueryVariables {
  filter?: PipelineRunsFilter | null;
  limit?: number | null;
}
