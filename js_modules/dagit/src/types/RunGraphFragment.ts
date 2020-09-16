// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { StepEventStatus } from "./globalTypes";

// ====================================================
// GraphQL fragment: RunGraphFragment
// ====================================================

export interface RunGraphFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export interface RunGraphFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunGraphFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunGraphFragment_stats_PythonError_cause | null;
}

export type RunGraphFragment_stats = RunGraphFragment_stats_PipelineRunStatsSnapshot | RunGraphFragment_stats_PythonError;

export interface RunGraphFragment_stepStats_materializations {
  __typename: "Materialization";
}

export interface RunGraphFragment_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface RunGraphFragment_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: RunGraphFragment_stepStats_materializations[];
  expectationResults: RunGraphFragment_stepStats_expectationResults[];
}

export interface RunGraphFragment {
  __typename: "PipelineRun";
  runId: string;
  stats: RunGraphFragment_stats;
  stepStats: RunGraphFragment_stepStats[];
}
