// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunTimeFragment
// ====================================================

export interface RunTimeFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface RunTimeFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunTimeFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunTimeFragment_stats_PythonError_cause | null;
}

export type RunTimeFragment_stats = RunTimeFragment_stats_PipelineRunStatsSnapshot | RunTimeFragment_stats_PythonError;

export interface RunTimeFragment {
  __typename: "PipelineRun";
  id: string;
  status: PipelineRunStatus;
  stats: RunTimeFragment_stats;
}
