/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorsRootQuery
// ====================================================

export interface SensorsRootQuery_sensorsOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SensorsRootQuery_sensorsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_sensorsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_sensorsOrError_PythonError_cause | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_typeSpecificData = SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_typeSpecificData_SensorData | SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_typeSpecificData_ScheduleData;

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error_cause | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_typeSpecificData | null;
  runs: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_runs[];
  ticks: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks[];
  runningCount: number;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_targets {
  __typename: "Target";
  pipelineName: string;
  solidSelection: string[] | null;
  mode: string;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_metadata_assetKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_metadata {
  __typename: "SensorMetadata";
  assetKeys: SensorsRootQuery_sensorsOrError_Sensors_results_metadata_assetKeys[] | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  description: string | null;
  minIntervalSeconds: number;
  nextTick: SensorsRootQuery_sensorsOrError_Sensors_results_nextTick | null;
  sensorState: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState;
  targets: SensorsRootQuery_sensorsOrError_Sensors_results_targets[] | null;
  metadata: SensorsRootQuery_sensorsOrError_Sensors_results_metadata;
}

export interface SensorsRootQuery_sensorsOrError_Sensors {
  __typename: "Sensors";
  results: SensorsRootQuery_sensorsOrError_Sensors_results[];
}

export type SensorsRootQuery_sensorsOrError = SensorsRootQuery_sensorsOrError_RepositoryNotFoundError | SensorsRootQuery_sensorsOrError_PythonError | SensorsRootQuery_sensorsOrError_Sensors;

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData = SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData | SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData;

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause | null;
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error | null;
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData | null;
  runs: SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs[];
  ticks: SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks[];
  runningCount: number;
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_unloadableInstigationStatesOrError_PythonError_cause | null;
}

export type SensorsRootQuery_unloadableInstigationStatesOrError = SensorsRootQuery_unloadableInstigationStatesOrError_InstigationStates | SensorsRootQuery_unloadableInstigationStatesOrError_PythonError;

export interface SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface SensorsRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface SensorsRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: SensorsRootQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface SensorsRootQuery_instance {
  __typename: "Instance";
  daemonHealth: SensorsRootQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface SensorsRootQuery {
  sensorsOrError: SensorsRootQuery_sensorsOrError;
  unloadableInstigationStatesOrError: SensorsRootQuery_unloadableInstigationStatesOrError;
  instance: SensorsRootQuery_instance;
}

export interface SensorsRootQueryVariables {
  repositorySelector: RepositorySelector;
  instigationType: InstigationType;
}
