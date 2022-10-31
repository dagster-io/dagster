/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunsRootQuery
// ====================================================

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_assetSelection {
  __typename: "AssetKey";
  path: string[];
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results {
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
  repositoryOrigin: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  assetSelection: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_assetSelection[] | null;
  tags: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_tags[];
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results[];
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PipelineRunsRootQuery_pipelineRunsOrError_PythonError_causes[];
}

export type PipelineRunsRootQuery_pipelineRunsOrError = PipelineRunsRootQuery_pipelineRunsOrError_Runs | PipelineRunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PipelineRunsRootQuery_pipelineRunsOrError_PythonError;

export interface PipelineRunsRootQuery {
  pipelineRunsOrError: PipelineRunsRootQuery_pipelineRunsOrError;
}

export interface PipelineRunsRootQueryVariables {
  limit?: number | null;
  cursor?: string | null;
  filter: RunsFilter;
}
