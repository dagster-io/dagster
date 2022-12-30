/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartSensor
// ====================================================

export interface StartSensor_startSensor_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "UnauthorizedError";
}

export interface StartSensor_startSensor_Sensor_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface StartSensor_startSensor_Sensor {
  __typename: "Sensor";
  id: string;
  sensorState: StartSensor_startSensor_Sensor_sensorState;
}

export interface StartSensor_startSensor_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface StartSensor_startSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: StartSensor_startSensor_PythonError_causes[];
}

export type StartSensor_startSensor = StartSensor_startSensor_SensorNotFoundError | StartSensor_startSensor_Sensor | StartSensor_startSensor_PythonError;

export interface StartSensor {
  startSensor: StartSensor_startSensor;
}

export interface StartSensorVariables {
  sensorSelector: SensorSelector;
}
