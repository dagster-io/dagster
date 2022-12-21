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

export interface StopSensor_stopSensor_PythonError_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface StopSensor_stopSensor_PythonError_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: StopSensor_stopSensor_PythonError_errorChain_error;
}

export interface StopSensor_stopSensor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: StopSensor_stopSensor_PythonError_errorChain[];
}

export type StopSensor_stopSensor = StopSensor_stopSensor_UnauthorizedError | StopSensor_stopSensor_StopSensorMutationResult | StopSensor_stopSensor_PythonError;

export interface StopSensor {
  stopSensor: StopSensor_stopSensor;
}

export interface StopSensorVariables {
  jobOriginId: string;
  jobSelectorId: string;
}
