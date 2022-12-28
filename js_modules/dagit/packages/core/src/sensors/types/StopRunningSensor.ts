/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopRunningSensor
// ====================================================

export interface StopRunningSensor_stopSensor_UnauthorizedError {
  __typename: "UnauthorizedError";
}

export interface StopRunningSensor_stopSensor_StopSensorMutationResult_instigationState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface StopRunningSensor_stopSensor_StopSensorMutationResult {
  __typename: "StopSensorMutationResult";
  instigationState: StopRunningSensor_stopSensor_StopSensorMutationResult_instigationState | null;
}

export interface StopRunningSensor_stopSensor_PythonError_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface StopRunningSensor_stopSensor_PythonError_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: StopRunningSensor_stopSensor_PythonError_errorChain_error;
}

export interface StopRunningSensor_stopSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: StopRunningSensor_stopSensor_PythonError_errorChain[];
}

export type StopRunningSensor_stopSensor = StopRunningSensor_stopSensor_UnauthorizedError | StopRunningSensor_stopSensor_StopSensorMutationResult | StopRunningSensor_stopSensor_PythonError;

export interface StopRunningSensor {
  stopSensor: StopRunningSensor_stopSensor;
}

export interface StopRunningSensorVariables {
  jobOriginId: string;
  jobSelectorId: string;
}
