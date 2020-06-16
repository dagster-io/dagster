// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RunStatsQuery
// ====================================================

export interface RunStatsQuery_pipelineRunOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunStatsQuery_pipelineRunOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunStatsQuery_pipelineRunOrError_PythonError_cause | null;
}

export interface RunStatsQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
  message: string;
}

export interface RunStatsQuery_pipelineRunOrError_PipelineRun_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  stepsSucceeded: number;
  stepsFailed: number;
  expectations: number;
  materializations: number;
}

export interface RunStatsQuery_pipelineRunOrError_PipelineRun_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunStatsQuery_pipelineRunOrError_PipelineRun_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunStatsQuery_pipelineRunOrError_PipelineRun_stats_PythonError_cause | null;
}

export type RunStatsQuery_pipelineRunOrError_PipelineRun_stats = RunStatsQuery_pipelineRunOrError_PipelineRun_stats_PipelineRunStatsSnapshot | RunStatsQuery_pipelineRunOrError_PipelineRun_stats_PythonError;

export interface RunStatsQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  runId: string;
  pipelineName: string;
  stats: RunStatsQuery_pipelineRunOrError_PipelineRun_stats;
}

export type RunStatsQuery_pipelineRunOrError = RunStatsQuery_pipelineRunOrError_PythonError | RunStatsQuery_pipelineRunOrError_PipelineRunNotFoundError | RunStatsQuery_pipelineRunOrError_PipelineRun;

export interface RunStatsQuery {
  pipelineRunOrError: RunStatsQuery_pipelineRunOrError;
}

export interface RunStatsQueryVariables {
  runId: string;
}
