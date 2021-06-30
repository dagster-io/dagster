// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewJobFragment
// ====================================================

export interface OverviewJobFragment_lastRuns_stats_PythonError {
  __typename: "PythonError";
}

export interface OverviewJobFragment_lastRuns_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
}

export type OverviewJobFragment_lastRuns_stats = OverviewJobFragment_lastRuns_stats_PythonError | OverviewJobFragment_lastRuns_stats_PipelineRunStatsSnapshot;

export interface OverviewJobFragment_lastRuns {
  __typename: "PipelineRun";
  id: string;
  stats: OverviewJobFragment_lastRuns_stats;
}

export interface OverviewJobFragment_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface OverviewJobFragment {
  __typename: "InstigationState";
  id: string;
  runsCount: number;
  lastRuns: OverviewJobFragment_lastRuns[];
  runs: OverviewJobFragment_runs[];
  status: InstigationStatus;
}
