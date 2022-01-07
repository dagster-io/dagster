/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, InstigationStatus } from "./../../types/globalTypes";

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

export interface OverviewJobFragment_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface OverviewJobFragment_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface OverviewJobFragment_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: OverviewJobFragment_schedules_futureTicks_results[];
}

export interface OverviewJobFragment_schedules {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  cronSchedule: string;
  scheduleState: OverviewJobFragment_schedules_scheduleState;
  executionTimezone: string | null;
  futureTicks: OverviewJobFragment_schedules_futureTicks;
}

export interface OverviewJobFragment_sensors_targets {
  __typename: "Target";
  pipelineName: string;
  mode: string;
}

export interface OverviewJobFragment_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface OverviewJobFragment_sensors {
  __typename: "Sensor";
  id: string;
  targets: OverviewJobFragment_sensors_targets[] | null;
  jobOriginId: string;
  name: string;
  sensorState: OverviewJobFragment_sensors_sensorState;
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
  schedules: OverviewJobFragment_schedules[];
  sensors: OverviewJobFragment_sensors[];
  modes: OverviewJobFragment_modes[];
}
