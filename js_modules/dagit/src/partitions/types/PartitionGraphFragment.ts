// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionGraphFragment
// ====================================================

export interface PartitionGraphFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export interface PartitionGraphFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionGraphFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionGraphFragment_stats_PythonError_cause | null;
}

export type PartitionGraphFragment_stats = PartitionGraphFragment_stats_PipelineRunStatsSnapshot | PartitionGraphFragment_stats_PythonError;

export interface PartitionGraphFragment_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionGraphFragment_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionGraphFragment_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: PartitionGraphFragment_stepStats_materializations[];
  expectationResults: PartitionGraphFragment_stepStats_expectationResults[];
}

export interface PartitionGraphFragment {
  __typename: "PipelineRun";
  runId: string;
  stats: PartitionGraphFragment_stats;
  stepStats: PartitionGraphFragment_stepStats[];
}
