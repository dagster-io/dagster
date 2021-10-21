// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunsRootQuery
// ====================================================

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats_PythonError_cause | null;
}

export type PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats = PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats_RunStatsSnapshot | PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats_PythonError;

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
  pipeline: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_pipeline;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  repositoryOrigin: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  tags: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_tags[];
  stats: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results_stats;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PipelineRunsRootQuery_pipelineRunsOrError_Runs_results[];
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface PipelineRunsRootQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
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
