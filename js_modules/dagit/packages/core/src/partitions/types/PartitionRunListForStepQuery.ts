// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionRunListForStepQuery
// ====================================================

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause | null;
}

export type PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats = PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results {
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
  tags: PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  stats: PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results_stats;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionRunListForStepQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionRunListForStepQuery_pipelineRunsOrError_PythonError_cause | null;
}

export type PartitionRunListForStepQuery_pipelineRunsOrError = PartitionRunListForStepQuery_pipelineRunsOrError_PipelineRuns | PartitionRunListForStepQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PartitionRunListForStepQuery_pipelineRunsOrError_PythonError;

export interface PartitionRunListForStepQuery {
  pipelineRunsOrError: PartitionRunListForStepQuery_pipelineRunsOrError;
}

export interface PartitionRunListForStepQueryVariables {
  filter: PipelineRunsFilter;
}
