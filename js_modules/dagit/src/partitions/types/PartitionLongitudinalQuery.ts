// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineRunStatus, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionLongitudinalQuery
// ====================================================

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats_PythonError_cause | null;
}

export type PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats_PipelineRunStatsSnapshot | PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats_PythonError;

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stepStats_materializations[];
  expectationResults: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stepStats_expectationResults[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs {
  __typename: "PipelineRun";
  runId: string;
  pipelineName: string;
  tags: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_tags[];
  stats: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stats;
  status: PipelineRunStatus;
  stepStats: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs_stepStats[];
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  solidSelection: string[] | null;
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
  runs: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause | null;
}

export type PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions | PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError;

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  name: string;
  partitionsOrError: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitionsOrError;
}

export type PartitionLongitudinalQuery_partitionSetOrError = PartitionLongitudinalQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionLongitudinalQuery_partitionSetOrError_PartitionSet;

export interface PartitionLongitudinalQuery {
  partitionSetOrError: PartitionLongitudinalQuery_partitionSetOrError;
}

export interface PartitionLongitudinalQueryVariables {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
  limit?: number | null;
  cursor?: string | null;
  reverse?: boolean | null;
}
