/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionSetLoaderQuery
// ====================================================

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause | null;
}

export type PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats = PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot | PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats_PythonError;

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stepStats_materializations[];
  expectationResults: PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stepStats_expectationResults[];
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  status: RunStatus;
  tags: PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_tags[];
  runId: string;
  stats: PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stats;
  stepStats: PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results_stepStats[];
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PartitionSetLoaderQuery_pipelineRunsOrError_Runs_results[];
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionSetLoaderQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionSetLoaderQuery_pipelineRunsOrError_PythonError_cause | null;
}

export type PartitionSetLoaderQuery_pipelineRunsOrError = PartitionSetLoaderQuery_pipelineRunsOrError_Runs | PartitionSetLoaderQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PartitionSetLoaderQuery_pipelineRunsOrError_PythonError;

export interface PartitionSetLoaderQuery {
  pipelineRunsOrError: PartitionSetLoaderQuery_pipelineRunsOrError;
}

export interface PartitionSetLoaderQueryVariables {
  filter: RunsFilter;
  cursor?: string | null;
  limit?: number | null;
}
