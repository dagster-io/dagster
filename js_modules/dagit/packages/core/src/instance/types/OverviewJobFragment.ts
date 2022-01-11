/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewJobFragment
// ====================================================

export interface OverviewJobFragment_runs_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface OverviewJobFragment_runs_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewJobFragment_runs_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: OverviewJobFragment_runs_stats_PythonError_cause | null;
}

export type OverviewJobFragment_runs_stats = OverviewJobFragment_runs_stats_RunStatsSnapshot | OverviewJobFragment_runs_stats_PythonError;

export interface OverviewJobFragment_runs {
  __typename: "Run";
  id: string;
  mode: string;
  runId: string;
  status: RunStatus;
  stats: OverviewJobFragment_runs_stats;
}

export interface OverviewJobFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface OverviewJobFragment {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  runs: OverviewJobFragment_runs[];
  modes: OverviewJobFragment_modes[];
}
