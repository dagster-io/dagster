// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector, JobTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleRootQuery
// ====================================================

export interface ScheduleRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface ScheduleRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface ScheduleRootQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_scheduler_PythonError_cause | null;
}

export type ScheduleRootQuery_scheduler = ScheduleRootQuery_scheduler_SchedulerNotDefinedError | ScheduleRootQuery_scheduler_Scheduler | ScheduleRootQuery_scheduler_PythonError;

export interface ScheduleRootQuery_scheduleOrError_Schedule_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData = ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: JobTickStatus;
  timestamp: number;
  tickSpecificData: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_tickSpecificData | null;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks[];
  runsCount: number;
  runs: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_futureTicks {
  __typename: "ScheduleFutureTicks";
  results: ScheduleRootQuery_scheduleOrError_Schedule_futureTicks_results[];
}

export interface ScheduleRootQuery_scheduleOrError_Schedule {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: ScheduleRootQuery_scheduleOrError_Schedule_partitionSet | null;
  scheduleState: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState | null;
  futureTicks: ScheduleRootQuery_scheduleOrError_Schedule_futureTicks;
}

export interface ScheduleRootQuery_scheduleOrError_ScheduleNotFoundError {
  __typename: "ScheduleNotFoundError";
  message: string;
}

export interface ScheduleRootQuery_scheduleOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type ScheduleRootQuery_scheduleOrError = ScheduleRootQuery_scheduleOrError_Schedule | ScheduleRootQuery_scheduleOrError_ScheduleNotFoundError | ScheduleRootQuery_scheduleOrError_PythonError;

export interface ScheduleRootQuery {
  scheduler: ScheduleRootQuery_scheduler;
  scheduleOrError: ScheduleRootQuery_scheduleOrError;
}

export interface ScheduleRootQueryVariables {
  scheduleSelector: ScheduleSelector;
}
