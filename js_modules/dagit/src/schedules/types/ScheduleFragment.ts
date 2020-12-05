// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleFragment
// ====================================================

export interface ScheduleFragment_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface ScheduleFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduleFragment_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduleFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type ScheduleFragment_scheduleState_ticks_tickSpecificData = ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | ScheduleFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface ScheduleFragment_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: JobTickStatus;
  timestamp: number;
  tickSpecificData: ScheduleFragment_scheduleState_ticks_tickSpecificData | null;
}

export interface ScheduleFragment_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleFragment_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: ScheduleFragment_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface ScheduleFragment_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: ScheduleFragment_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: ScheduleFragment_scheduleState_ticks[];
  runsCount: number;
  runs: ScheduleFragment_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface ScheduleFragment_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface ScheduleFragment_futureTicks {
  __typename: "ScheduleFutureTicks";
  results: ScheduleFragment_futureTicks_results[];
}

export interface ScheduleFragment {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: ScheduleFragment_partitionSet | null;
  scheduleState: ScheduleFragment_scheduleState | null;
  futureTicks: ScheduleFragment_futureTicks;
}
