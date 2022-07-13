/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulerInfoQuery
// ====================================================

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes[];
}

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface SchedulerInfoQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface SchedulerInfoQuery_instance {
  __typename: "Instance";
  daemonHealth: SchedulerInfoQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData = SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_SensorData | SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_ScheduleData;

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_causes[];
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData | null;
  runs: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  description: string | null;
  partitionSet: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  schedules: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_schedules[];
  displayMetadata: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata[];
}

export interface SchedulerInfoQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: SchedulerInfoQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface SchedulerInfoQuery_repositoriesOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerInfoQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SchedulerInfoQuery_repositoriesOrError_PythonError_causes[];
}

export type SchedulerInfoQuery_repositoriesOrError = SchedulerInfoQuery_repositoriesOrError_RepositoryConnection | SchedulerInfoQuery_repositoriesOrError_PythonError;

export interface SchedulerInfoQuery {
  instance: SchedulerInfoQuery_instance;
  repositoriesOrError: SchedulerInfoQuery_repositoriesOrError;
}
