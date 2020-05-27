// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunStatsDetailFragment
// ====================================================

export interface RunStatsDetailFragment_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface RunStatsDetailFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  stepsSucceeded: number;
  stepsFailed: number;
  expectations: number;
  materializations: number;
}

export interface RunStatsDetailFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunStatsDetailFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunStatsDetailFragment_stats_PythonError_cause | null;
}

export type RunStatsDetailFragment_stats = RunStatsDetailFragment_stats_PipelineRunStatsSnapshot | RunStatsDetailFragment_stats_PythonError;

export interface RunStatsDetailFragment {
  __typename: "PipelineRun";
  runId: string;
  pipeline: RunStatsDetailFragment_pipeline;
  stats: RunStatsDetailFragment_stats;
}
