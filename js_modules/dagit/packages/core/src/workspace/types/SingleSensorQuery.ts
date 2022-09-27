/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, InstigationTickStatus, RunStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SingleSensorQuery
// ====================================================

export interface SingleSensorQuery_sensorOrError_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "UnauthorizedError" | "PythonError";
}

export interface SingleSensorQuery_sensorOrError_Sensor_targets {
  __typename: "Target";
  pipelineName: string;
}

export interface SingleSensorQuery_sensorOrError_Sensor_metadata_assetKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface SingleSensorQuery_sensorOrError_Sensor_metadata {
  __typename: "SensorMetadata";
  assetKeys: SingleSensorQuery_sensorOrError_Sensor_metadata_assetKeys[] | null;
}

export interface SingleSensorQuery_sensorOrError_Sensor_sensorState_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SingleSensorQuery_sensorOrError_Sensor_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SingleSensorQuery_sensorOrError_Sensor_sensorState_ticks_error_causes[];
}

export interface SingleSensorQuery_sensorOrError_Sensor_sensorState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SingleSensorQuery_sensorOrError_Sensor_sensorState_ticks_error | null;
}

export interface SingleSensorQuery_sensorOrError_Sensor_sensorState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SingleSensorQuery_sensorOrError_Sensor_sensorState_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SingleSensorQuery_sensorOrError_Sensor_sensorState {
  __typename: "InstigationState";
  id: string;
  runningCount: number;
  ticks: SingleSensorQuery_sensorOrError_Sensor_sensorState_ticks[];
  runs: SingleSensorQuery_sensorOrError_Sensor_sensorState_runs[];
  nextTick: SingleSensorQuery_sensorOrError_Sensor_sensorState_nextTick | null;
  selectorId: string;
  status: InstigationStatus;
}

export interface SingleSensorQuery_sensorOrError_Sensor {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: SingleSensorQuery_sensorOrError_Sensor_targets[] | null;
  metadata: SingleSensorQuery_sensorOrError_Sensor_metadata;
  minIntervalSeconds: number;
  description: string | null;
  sensorState: SingleSensorQuery_sensorOrError_Sensor_sensorState;
  jobOriginId: string;
}

export type SingleSensorQuery_sensorOrError = SingleSensorQuery_sensorOrError_SensorNotFoundError | SingleSensorQuery_sensorOrError_Sensor;

export interface SingleSensorQuery {
  sensorOrError: SingleSensorQuery_sensorOrError;
}

export interface SingleSensorQueryVariables {
  selector: SensorSelector;
}
