/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionStepLoaderQuery
// ====================================================

export interface PartitionStepLoaderQuery_pipelineRunsOrError_Runs_results_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
}

export interface PartitionStepLoaderQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionStepLoaderQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  stepStats: PartitionStepLoaderQuery_pipelineRunsOrError_Runs_results_stepStats[];
  tags: PartitionStepLoaderQuery_pipelineRunsOrError_Runs_results_tags[];
}

export interface PartitionStepLoaderQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PartitionStepLoaderQuery_pipelineRunsOrError_Runs_results[];
}

export interface PartitionStepLoaderQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PartitionStepLoaderQuery_pipelineRunsOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionStepLoaderQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionStepLoaderQuery_pipelineRunsOrError_PythonError_causes[];
}

export type PartitionStepLoaderQuery_pipelineRunsOrError = PartitionStepLoaderQuery_pipelineRunsOrError_Runs | PartitionStepLoaderQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PartitionStepLoaderQuery_pipelineRunsOrError_PythonError;

export interface PartitionStepLoaderQuery {
  pipelineRunsOrError: PartitionStepLoaderQuery_pipelineRunsOrError;
}

export interface PartitionStepLoaderQueryVariables {
  filter: RunsFilter;
  cursor?: string | null;
  limit?: number | null;
}
