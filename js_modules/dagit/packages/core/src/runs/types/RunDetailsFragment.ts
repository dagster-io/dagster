// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunDetailsFragment
// ====================================================

export interface RunDetailsFragment_stats_PythonError {
  __typename: "PythonError";
}

export interface RunDetailsFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
  startTime: number | null;
}

export type RunDetailsFragment_stats = RunDetailsFragment_stats_PythonError | RunDetailsFragment_stats_PipelineRunStatsSnapshot;

export interface RunDetailsFragment {
  __typename: "Run";
  id: string;
  stats: RunDetailsFragment_stats;
  status: PipelineRunStatus;
}
