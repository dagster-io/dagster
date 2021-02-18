// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionProgressQuery
// ====================================================

export interface PartitionProgressQuery_pipelineRunsOrError_PipelineRuns_results {
  __typename: "PipelineRun";
  id: string;
  canTerminate: boolean;
  status: PipelineRunStatus;
}

export interface PartitionProgressQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: PartitionProgressQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export interface PartitionProgressQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PartitionProgressQuery_pipelineRunsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionProgressQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionProgressQuery_pipelineRunsOrError_PythonError_cause | null;
}

export type PartitionProgressQuery_pipelineRunsOrError = PartitionProgressQuery_pipelineRunsOrError_PipelineRuns | PartitionProgressQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PartitionProgressQuery_pipelineRunsOrError_PythonError;

export interface PartitionProgressQuery {
  pipelineRunsOrError: PartitionProgressQuery_pipelineRunsOrError;
}

export interface PartitionProgressQueryVariables {
  filter: PipelineRunsFilter;
  limit?: number | null;
}
