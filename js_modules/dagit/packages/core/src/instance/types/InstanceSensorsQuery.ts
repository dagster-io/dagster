/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceSensorsQuery
// ====================================================

export interface InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceSensorsQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceSensorsQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceSensorsQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_typeSpecificData = InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_typeSpecificData_SensorData | InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_typeSpecificData_ScheduleData;

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_typeSpecificData | null;
  runs: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs[];
  ticks: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks[];
  runningCount: number;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_targets {
  __typename: "Target";
  pipelineName: string;
  solidSelection: string[] | null;
  mode: string;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_metadata_assetKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_metadata {
  __typename: "SensorMetadata";
  assetKeys: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_metadata_assetKeys[] | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  description: string | null;
  minIntervalSeconds: number;
  nextTick: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick | null;
  sensorState: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState;
  targets: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_targets[] | null;
  metadata: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_metadata;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  displayMetadata: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata[];
  sensors: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors[];
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface InstanceSensorsQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_repositoriesOrError_PythonError_cause | null;
}

export type InstanceSensorsQuery_repositoriesOrError = InstanceSensorsQuery_repositoriesOrError_RepositoryConnection | InstanceSensorsQuery_repositoriesOrError_PythonError;

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData = InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData | InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData;

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause | null;
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error | null;
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData | null;
  runs: InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs[];
  ticks: InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks[];
  runningCount: number;
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_unloadableInstigationStatesOrError_PythonError_cause | null;
}

export type InstanceSensorsQuery_unloadableInstigationStatesOrError = InstanceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates | InstanceSensorsQuery_unloadableInstigationStatesOrError_PythonError;

export interface InstanceSensorsQuery {
  instance: InstanceSensorsQuery_instance;
  repositoriesOrError: InstanceSensorsQuery_repositoriesOrError;
  unloadableInstigationStatesOrError: InstanceSensorsQuery_unloadableInstigationStatesOrError;
}
