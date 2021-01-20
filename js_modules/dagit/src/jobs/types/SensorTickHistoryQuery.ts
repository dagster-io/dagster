// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, JobType, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorTickHistoryQuery
// ====================================================

export interface SensorTickHistoryQuery_sensorOrError_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "PythonError";
}

export interface SensorTickHistoryQuery_sensorOrError_Sensor_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorTickHistoryQuery_sensorOrError_Sensor_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorTickHistoryQuery_sensorOrError_Sensor_sensorState_ticks_error_cause | null;
}

export interface SensorTickHistoryQuery_sensorOrError_Sensor_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: SensorTickHistoryQuery_sensorOrError_Sensor_sensorState_ticks_error | null;
}

export interface SensorTickHistoryQuery_sensorOrError_Sensor_sensorState {
  __typename: "JobState";
  id: string;
  jobType: JobType;
  ticks: SensorTickHistoryQuery_sensorOrError_Sensor_sensorState_ticks[];
}

export interface SensorTickHistoryQuery_sensorOrError_Sensor {
  __typename: "Sensor";
  id: string;
  sensorState: SensorTickHistoryQuery_sensorOrError_Sensor_sensorState;
}

export type SensorTickHistoryQuery_sensorOrError = SensorTickHistoryQuery_sensorOrError_SensorNotFoundError | SensorTickHistoryQuery_sensorOrError_Sensor;

export interface SensorTickHistoryQuery {
  sensorOrError: SensorTickHistoryQuery_sensorOrError;
}

export interface SensorTickHistoryQueryVariables {
  sensorSelector: SensorSelector;
}
