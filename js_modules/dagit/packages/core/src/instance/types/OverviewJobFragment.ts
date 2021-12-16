/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewJobFragment
// ====================================================

export interface OverviewJobFragment_runs_assets_key {
  __typename: "AssetKey";
  path: string[];
}

export interface OverviewJobFragment_runs_assets {
  __typename: "Asset";
  id: string;
  key: OverviewJobFragment_runs_assets_key;
}

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
  assets: OverviewJobFragment_runs_assets[];
  stats: OverviewJobFragment_runs_stats;
}

export interface OverviewJobFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface OverviewJobFragment_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface OverviewJobFragment_schedules {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  scheduleState: OverviewJobFragment_schedules_scheduleState;
  cronSchedule: string;
}

export interface OverviewJobFragment_sensors_targets {
  __typename: "Target";
  mode: string;
  pipelineName: string;
}

export interface OverviewJobFragment_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface OverviewJobFragment_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: OverviewJobFragment_sensors_targets[] | null;
  sensorState: OverviewJobFragment_sensors_sensorState;
  jobOriginId: string;
}

export interface OverviewJobFragment {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  runs: OverviewJobFragment_runs[];
  modes: OverviewJobFragment_modes[];
  schedules: OverviewJobFragment_schedules[];
  sensors: OverviewJobFragment_sensors[];
}
