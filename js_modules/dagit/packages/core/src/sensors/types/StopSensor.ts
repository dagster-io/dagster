/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSensor
// ====================================================

export interface StopSensor_stopSensor_UnauthorizedError {
  __typename: "UnauthorizedError";
}

export interface StopSensor_stopSensor_StopSensorMutationResult_instigationState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface StopSensor_stopSensor_StopSensorMutationResult {
  __typename: "StopSensorMutationResult";
  instigationState: StopSensor_stopSensor_StopSensorMutationResult_instigationState | null;
}

export interface StopSensor_stopSensor_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface StopSensor_stopSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: StopSensor_stopSensor_PythonError_causes[];
}

export type StopSensor_stopSensor = StopSensor_stopSensor_UnauthorizedError | StopSensor_stopSensor_StopSensorMutationResult | StopSensor_stopSensor_PythonError;

export interface StopSensor {
  stopSensor: StopSensor_stopSensor;
}

export interface StopSensorVariables {
  jobOriginId: string;
  jobSelectorId: string;
}
