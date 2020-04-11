// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionRunsQuery
// ====================================================

export interface PartitionRunsQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
  endTime: number | null;
}

export type PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stats = PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError | PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot;

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs_dependsOn[];
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps_inputs[];
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan {
  __typename: "ExecutionPlan";
  steps: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results {
  __typename: "PipelineRun";
  runId: string;
  tags: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  stats: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stats;
  stepStats: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_stepStats[];
  status: PipelineRunStatus;
  executionPlan: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_executionPlan | null;
}

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export type PartitionRunsQuery_pipelineRunsOrError = PartitionRunsQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PartitionRunsQuery_pipelineRunsOrError_PipelineRuns;

export interface PartitionRunsQuery {
  pipelineRunsOrError: PartitionRunsQuery_pipelineRunsOrError;
}

export interface PartitionRunsQueryVariables {
  partitionSetName: string;
}
