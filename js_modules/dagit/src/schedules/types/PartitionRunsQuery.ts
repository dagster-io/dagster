// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

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

export interface PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results {
  __typename: "PipelineRun";
  runId: string;
  tags: PartitionRunsQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
  status: PipelineRunStatus;
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
