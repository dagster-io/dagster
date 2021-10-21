// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PreviousRunsForScheduleQuery
// ====================================================

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause | null;
}

export type PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats = PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot | PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats_PythonError;

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipeline: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_pipeline;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  repositoryOrigin: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  tags: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_tags[];
  stats: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_stats;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results[];
}

export type PreviousRunsForScheduleQuery_pipelineRunsOrError = PreviousRunsForScheduleQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs;

export interface PreviousRunsForScheduleQuery {
  pipelineRunsOrError: PreviousRunsForScheduleQuery_pipelineRunsOrError;
}

export interface PreviousRunsForScheduleQueryVariables {
  filter?: PipelineRunsFilter | null;
  limit?: number | null;
}
