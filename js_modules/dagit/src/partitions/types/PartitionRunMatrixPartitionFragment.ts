// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionRunMatrixPartitionFragment
// ====================================================

export interface PartitionRunMatrixPartitionFragment_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionRunMatrixPartitionFragment_runs_stats_PythonError {
  __typename: "PythonError";
}

export interface PartitionRunMatrixPartitionFragment_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
}

export type PartitionRunMatrixPartitionFragment_runs_stats = PartitionRunMatrixPartitionFragment_runs_stats_PythonError | PartitionRunMatrixPartitionFragment_runs_stats_PipelineRunStatsSnapshot;

export interface PartitionRunMatrixPartitionFragment_runs_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionRunMatrixPartitionFragment_runs_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionRunMatrixPartitionFragment_runs_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  status: StepEventStatus | null;
  materializations: PartitionRunMatrixPartitionFragment_runs_stepStats_materializations[];
  expectationResults: PartitionRunMatrixPartitionFragment_runs_stepStats_expectationResults[];
}

export interface PartitionRunMatrixPartitionFragment_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: PartitionRunMatrixPartitionFragment_runs_tags[];
  stats: PartitionRunMatrixPartitionFragment_runs_stats;
  stepStats: PartitionRunMatrixPartitionFragment_runs_stepStats[];
}

export interface PartitionRunMatrixPartitionFragment {
  __typename: "Partition";
  name: string;
  runs: PartitionRunMatrixPartitionFragment_runs[];
}
