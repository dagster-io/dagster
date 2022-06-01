/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulesRootQuery_repositoryOrError_Repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_typeSpecificData = SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_typeSpecificData_SensorData | SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_typeSpecificData_ScheduleData;

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error_cause | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_typeSpecificData | null;
  runs: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_runs[];
  ticks: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks_results[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  description: string | null;
  partitionSet: SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet | null;
  scheduleState: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState;
  futureTicks: SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: SchedulesRootQuery_repositoryOrError_Repository_location;
  schedules: SchedulesRootQuery_repositoryOrError_Repository_schedules[];
  displayMetadata: SchedulesRootQuery_repositoryOrError_Repository_displayMetadata[];
}

export interface SchedulesRootQuery_repositoryOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_repositoryOrError_PythonError_cause | null;
}

export type SchedulesRootQuery_repositoryOrError = SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError | SchedulesRootQuery_repositoryOrError_Repository | SchedulesRootQuery_repositoryOrError_PythonError;

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData = SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData | SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData;

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause | null;
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error | null;
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData | null;
  runs: SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs[];
  ticks: SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks[];
  runningCount: number;
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_unloadableInstigationStatesOrError_PythonError_cause | null;
}

export type SchedulesRootQuery_unloadableInstigationStatesOrError = SchedulesRootQuery_unloadableInstigationStatesOrError_InstigationStates | SchedulesRootQuery_unloadableInstigationStatesOrError_PythonError;

export interface SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface SchedulesRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface SchedulesRootQuery_instance {
  __typename: "Instance";
  daemonHealth: SchedulesRootQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface SchedulesRootQuery {
  repositoryOrError: SchedulesRootQuery_repositoryOrError;
  unloadableInstigationStatesOrError: SchedulesRootQuery_unloadableInstigationStatesOrError;
  instance: SchedulesRootQuery_instance;
}

export interface SchedulesRootQueryVariables {
  repositorySelector: RepositorySelector;
  instigationType: InstigationType;
}
