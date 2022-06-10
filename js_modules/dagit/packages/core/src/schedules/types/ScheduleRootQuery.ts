/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector, InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleRootQuery
// ====================================================

export interface ScheduleRootQuery_scheduleOrError_Schedule_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_typeSpecificData = ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_typeSpecificData_SensorData | ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_typeSpecificData_ScheduleData;

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_error_cause | null;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks_error | null;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_typeSpecificData | null;
  runs: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_runs[];
  ticks: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState_ticks[];
  runningCount: number;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface ScheduleRootQuery_scheduleOrError_Schedule_futureTicks {
  __typename: "FutureInstigationTicks";
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
  description: string | null;
  partitionSet: ScheduleRootQuery_scheduleOrError_Schedule_partitionSet | null;
  scheduleState: ScheduleRootQuery_scheduleOrError_Schedule_scheduleState;
  futureTicks: ScheduleRootQuery_scheduleOrError_Schedule_futureTicks;
}

export interface ScheduleRootQuery_scheduleOrError_ScheduleNotFoundError {
  __typename: "ScheduleNotFoundError";
  message: string;
}

export interface ScheduleRootQuery_scheduleOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_scheduleOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_scheduleOrError_PythonError_cause | null;
}

export type ScheduleRootQuery_scheduleOrError = ScheduleRootQuery_scheduleOrError_Schedule | ScheduleRootQuery_scheduleOrError_ScheduleNotFoundError | ScheduleRootQuery_scheduleOrError_PythonError;

export interface ScheduleRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface ScheduleRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: ScheduleRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface ScheduleRootQuery_instance_daemonHealth_daemonStatus {
  __typename: "DaemonStatus";
  id: string;
  healthy: boolean | null;
}

export interface ScheduleRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: ScheduleRootQuery_instance_daemonHealth_allDaemonStatuses[];
  daemonStatus: ScheduleRootQuery_instance_daemonHealth_daemonStatus;
}

export interface ScheduleRootQuery_instance {
  __typename: "Instance";
  daemonHealth: ScheduleRootQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface ScheduleRootQuery {
  scheduleOrError: ScheduleRootQuery_scheduleOrError;
  instance: ScheduleRootQuery_instance;
}

export interface ScheduleRootQueryVariables {
  scheduleSelector: ScheduleSelector;
}
