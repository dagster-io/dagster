/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceSchedulesQuery
// ====================================================

export interface InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes[];
}

export interface InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceSchedulesQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceSchedulesQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceSchedulesQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData = InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_SensorData | InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData_ScheduleData;

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_causes[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_typeSpecificData | null;
  runs: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  description: string | null;
  partitionSet: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  displayMetadata: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata[];
  schedules: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceSchedulesQuery_repositoriesOrError_PythonError_causes[];
}

export type InstanceSchedulesQuery_repositoriesOrError = InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection | InstanceSchedulesQuery_repositoriesOrError_PythonError;

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData = InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData | InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData;

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_causes[];
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error | null;
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData | null;
  runs: InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs[];
  ticks: InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks[];
  runningCount: number;
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceSchedulesQuery_unloadableInstigationStatesOrError_PythonError_causes[];
}

export type InstanceSchedulesQuery_unloadableInstigationStatesOrError = InstanceSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates | InstanceSchedulesQuery_unloadableInstigationStatesOrError_PythonError;

export interface InstanceSchedulesQuery {
  instance: InstanceSchedulesQuery_instance;
  repositoriesOrError: InstanceSchedulesQuery_repositoriesOrError;
  unloadableInstigationStatesOrError: InstanceSchedulesQuery_unloadableInstigationStatesOrError;
}
