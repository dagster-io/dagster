// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewInstigationFragment
// ====================================================

export interface OverviewInstigationFragment_lastRuns_stats_PythonError {
  __typename: "PythonError";
}

export interface OverviewInstigationFragment_lastRuns_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
}

export type OverviewInstigationFragment_lastRuns_stats = OverviewInstigationFragment_lastRuns_stats_PythonError | OverviewInstigationFragment_lastRuns_stats_PipelineRunStatsSnapshot;

export interface OverviewInstigationFragment_lastRuns {
  __typename: "PipelineRun";
  id: string;
  stats: OverviewInstigationFragment_lastRuns_stats;
}

export interface OverviewInstigationFragment_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface OverviewInstigationFragment {
  __typename: "InstigationState";
  id: string;
  runsCount: number;
  lastRuns: OverviewInstigationFragment_lastRuns[];
  runs: OverviewInstigationFragment_runs[];
  status: InstigationStatus;
}
