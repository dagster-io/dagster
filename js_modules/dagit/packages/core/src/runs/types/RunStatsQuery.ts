/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RunStatsQuery
// ====================================================

export interface RunStatsQuery_pipelineRunOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunStatsQuery_pipelineRunOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RunStatsQuery_pipelineRunOrError_PythonError_causes[];
}

export interface RunStatsQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError";
  message: string;
}

export interface RunStatsQuery_pipelineRunOrError_Run_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  stepsSucceeded: number;
  stepsFailed: number;
  expectations: number;
  materializations: number;
}

export interface RunStatsQuery_pipelineRunOrError_Run_stats_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunStatsQuery_pipelineRunOrError_Run_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RunStatsQuery_pipelineRunOrError_Run_stats_PythonError_causes[];
}

export type RunStatsQuery_pipelineRunOrError_Run_stats = RunStatsQuery_pipelineRunOrError_Run_stats_RunStatsSnapshot | RunStatsQuery_pipelineRunOrError_Run_stats_PythonError;

export interface RunStatsQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  pipelineName: string;
  stats: RunStatsQuery_pipelineRunOrError_Run_stats;
}

export type RunStatsQuery_pipelineRunOrError = RunStatsQuery_pipelineRunOrError_PythonError | RunStatsQuery_pipelineRunOrError_RunNotFoundError | RunStatsQuery_pipelineRunOrError_Run;

export interface RunStatsQuery {
  pipelineRunOrError: RunStatsQuery_pipelineRunOrError;
}

export interface RunStatsQueryVariables {
  runId: string;
}
