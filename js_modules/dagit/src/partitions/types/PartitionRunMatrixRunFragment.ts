// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionRunMatrixRunFragment
// ====================================================

export interface PartitionRunMatrixRunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionRunMatrixRunFragment_stats_PythonError {
  __typename: "PythonError";
}

export interface PartitionRunMatrixRunFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
}

export type PartitionRunMatrixRunFragment_stats = PartitionRunMatrixRunFragment_stats_PythonError | PartitionRunMatrixRunFragment_stats_PipelineRunStatsSnapshot;

export interface PartitionRunMatrixRunFragment_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionRunMatrixRunFragment_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionRunMatrixRunFragment_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  status: StepEventStatus | null;
  materializations: PartitionRunMatrixRunFragment_stepStats_materializations[];
  expectationResults: PartitionRunMatrixRunFragment_stepStats_expectationResults[];
}

export interface PartitionRunMatrixRunFragment {
  __typename: "PipelineRun";
  runId: string;
  tags: PartitionRunMatrixRunFragment_tags[];
  stats: PartitionRunMatrixRunFragment_stats;
  stepStats: PartitionRunMatrixRunFragment_stepStats[];
}
