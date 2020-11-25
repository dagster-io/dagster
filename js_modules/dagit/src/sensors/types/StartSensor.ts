// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartSensor
// ====================================================

export interface StartSensor_startSensor_SensorNotFoundError {
  __typename: "SensorNotFoundError";
}

export interface StartSensor_startSensor_Sensor {
  __typename: "Sensor";
  id: string;
  status: JobStatus;
}

export interface StartSensor_startSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StartSensor_startSensor = StartSensor_startSensor_SensorNotFoundError | StartSensor_startSensor_Sensor | StartSensor_startSensor_PythonError;

export interface StartSensor {
  startSensor: StartSensor_startSensor;
}

export interface StartSensorVariables {
  sensorSelector: SensorSelector;
}
