// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSensor
// ====================================================

export interface StopSensor_stopSensor_SensorNotFoundError {
  __typename: "SensorNotFoundError";
}

export interface StopSensor_stopSensor_Sensor {
  __typename: "Sensor";
  id: string;
  status: JobStatus;
}

export interface StopSensor_stopSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StopSensor_stopSensor = StopSensor_stopSensor_SensorNotFoundError | StopSensor_stopSensor_Sensor | StopSensor_stopSensor_PythonError;

export interface StopSensor {
  stopSensor: StopSensor_stopSensor;
}

export interface StopSensorVariables {
  sensorSelector: SensorSelector;
}
