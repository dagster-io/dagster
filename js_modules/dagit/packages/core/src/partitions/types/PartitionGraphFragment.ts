/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionGraphFragment
// ====================================================

export interface PartitionGraphFragment_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export interface PartitionGraphFragment_stats_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionGraphFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionGraphFragment_stats_PythonError_causes[];
}

export type PartitionGraphFragment_stats = PartitionGraphFragment_stats_RunStatsSnapshot | PartitionGraphFragment_stats_PythonError;

export interface PartitionGraphFragment_stepStats_materializations {
  __typename: "MaterializationEvent";
}

export interface PartitionGraphFragment_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionGraphFragment_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
  materializations: PartitionGraphFragment_stepStats_materializations[];
  expectationResults: PartitionGraphFragment_stepStats_expectationResults[];
}

export interface PartitionGraphFragment {
  __typename: "Run";
  id: string;
  runId: string;
  stats: PartitionGraphFragment_stats;
  stepStats: PartitionGraphFragment_stepStats[];
}
