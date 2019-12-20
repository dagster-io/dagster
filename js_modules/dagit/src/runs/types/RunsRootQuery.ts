// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunsFilter, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunsRootQuery
// ====================================================

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline_Pipeline_solids[];
}

export type RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline = RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline_UnknownPipeline | RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline_Pipeline;

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  stepsSucceeded: number;
  stepsFailed: number;
  startTime: number | null;
  endTime: number | null;
  expectations: number;
  materializations: number;
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats = RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns_results {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canCancel: boolean;
  mode: string;
  environmentConfigYaml: string;
  pipeline: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_pipeline;
  stats: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_stats;
  tags: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results_tags[];
}

export interface RunsRootQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: RunsRootQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export interface RunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError";
  message: string;
}

export interface RunsRootQuery_pipelineRunsOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type RunsRootQuery_pipelineRunsOrError = RunsRootQuery_pipelineRunsOrError_PipelineRuns | RunsRootQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | RunsRootQuery_pipelineRunsOrError_PythonError;

export interface RunsRootQuery {
  pipelineRunsOrError: RunsRootQuery_pipelineRunsOrError;
}

export interface RunsRootQueryVariables {
  limit?: number | null;
  cursor?: string | null;
  filter: PipelineRunsFilter;
}
