/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorRootQuery
// ====================================================

export interface SensorRootQuery_sensorOrError_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "UnauthorizedError" | "PythonError";
}

export interface SensorRootQuery_sensorOrError_Sensor_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData = SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_SensorData | SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData_ScheduleData;

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error_causes[];
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: SensorRootQuery_sensorOrError_Sensor_sensorState_typeSpecificData | null;
  runs: SensorRootQuery_sensorOrError_Sensor_sensorState_runs[];
  ticks: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks[];
  runningCount: number;
}

export interface SensorRootQuery_sensorOrError_Sensor_targets {
  __typename: "Target";
  pipelineName: string;
  solidSelection: string[] | null;
  mode: string;
}

export interface SensorRootQuery_sensorOrError_Sensor_metadata_assetKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface SensorRootQuery_sensorOrError_Sensor_metadata {
  __typename: "SensorMetadata";
  assetKeys: SensorRootQuery_sensorOrError_Sensor_metadata_assetKeys[] | null;
}

export interface SensorRootQuery_sensorOrError_Sensor {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  description: string | null;
  minIntervalSeconds: number;
  nextTick: SensorRootQuery_sensorOrError_Sensor_nextTick | null;
  sensorState: SensorRootQuery_sensorOrError_Sensor_sensorState;
  targets: SensorRootQuery_sensorOrError_Sensor_targets[] | null;
  metadata: SensorRootQuery_sensorOrError_Sensor_metadata;
}

export type SensorRootQuery_sensorOrError = SensorRootQuery_sensorOrError_SensorNotFoundError | SensorRootQuery_sensorOrError_Sensor;

export interface SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes[];
}

export interface SensorRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SensorRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface SensorRootQuery_instance_daemonHealth_daemonStatus {
  __typename: "DaemonStatus";
  id: string;
  healthy: boolean | null;
}

export interface SensorRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: SensorRootQuery_instance_daemonHealth_allDaemonStatuses[];
  daemonStatus: SensorRootQuery_instance_daemonHealth_daemonStatus;
}

export interface SensorRootQuery_instance {
  __typename: "Instance";
  daemonHealth: SensorRootQuery_instance_daemonHealth;
  hasInfo: boolean;
}

export interface SensorRootQuery {
  sensorOrError: SensorRootQuery_sensorOrError;
  instance: SensorRootQuery_instance;
}

export interface SensorRootQueryVariables {
  sensorSelector: SensorSelector;
}
