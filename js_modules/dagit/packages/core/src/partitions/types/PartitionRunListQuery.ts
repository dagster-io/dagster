/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionRunListQuery
// ====================================================

export interface PartitionRunListQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PartitionRunListQuery_pipelineRunsOrError_Runs_results_assetSelection {
  __typename: "AssetKey";
  path: string[];
}

export interface PartitionRunListQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionRunListQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  repositoryOrigin: PartitionRunListQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  assetSelection: PartitionRunListQuery_pipelineRunsOrError_Runs_results_assetSelection[] | null;
  tags: PartitionRunListQuery_pipelineRunsOrError_Runs_results_tags[];
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface PartitionRunListQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PartitionRunListQuery_pipelineRunsOrError_Runs_results[];
}

export interface PartitionRunListQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PartitionRunListQuery_pipelineRunsOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionRunListQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionRunListQuery_pipelineRunsOrError_PythonError_causes[];
}

export type PartitionRunListQuery_pipelineRunsOrError = PartitionRunListQuery_pipelineRunsOrError_Runs | PartitionRunListQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PartitionRunListQuery_pipelineRunsOrError_PythonError;

export interface PartitionRunListQuery {
  pipelineRunsOrError: PartitionRunListQuery_pipelineRunsOrError;
}

export interface PartitionRunListQueryVariables {
  filter: RunsFilter;
}
