// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSensor
// ====================================================

export interface StopSensor_stopSensor_StopSensorMutationResult_jobState {
  __typename: "JobState";
  id: string;
  status: JobStatus;
}

export interface StopSensor_stopSensor_StopSensorMutationResult {
  __typename: "StopSensorMutationResult";
  jobState: StopSensor_stopSensor_StopSensorMutationResult_jobState | null;
}

export interface StopSensor_stopSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StopSensor_stopSensor = StopSensor_stopSensor_StopSensorMutationResult | StopSensor_stopSensor_PythonError;

export interface StopSensor {
  stopSensor: StopSensor_stopSensor;
}

export interface StopSensorVariables {
  jobOriginId: string;
}
