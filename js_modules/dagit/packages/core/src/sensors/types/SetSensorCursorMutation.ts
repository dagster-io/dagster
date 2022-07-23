/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SetSensorCursorMutation
// ====================================================

export interface SetSensorCursorMutation_setSensorCursor_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "UnauthorizedError";
}

export interface SetSensorCursorMutation_setSensorCursor_Sensor_sensorState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
}

export interface SetSensorCursorMutation_setSensorCursor_Sensor_sensorState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastCursor: string | null;
}

export type SetSensorCursorMutation_setSensorCursor_Sensor_sensorState_typeSpecificData = SetSensorCursorMutation_setSensorCursor_Sensor_sensorState_typeSpecificData_ScheduleData | SetSensorCursorMutation_setSensorCursor_Sensor_sensorState_typeSpecificData_SensorData;

export interface SetSensorCursorMutation_setSensorCursor_Sensor_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  typeSpecificData: SetSensorCursorMutation_setSensorCursor_Sensor_sensorState_typeSpecificData | null;
}

export interface SetSensorCursorMutation_setSensorCursor_Sensor {
  __typename: "Sensor";
  id: string;
  sensorState: SetSensorCursorMutation_setSensorCursor_Sensor_sensorState;
}

export interface SetSensorCursorMutation_setSensorCursor_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SetSensorCursorMutation_setSensorCursor_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SetSensorCursorMutation_setSensorCursor_PythonError_causes[];
}

export type SetSensorCursorMutation_setSensorCursor = SetSensorCursorMutation_setSensorCursor_SensorNotFoundError | SetSensorCursorMutation_setSensorCursor_Sensor | SetSensorCursorMutation_setSensorCursor_PythonError;

export interface SetSensorCursorMutation {
  setSensorCursor: SetSensorCursorMutation_setSensorCursor;
}

export interface SetSensorCursorMutationVariables {
  sensorSelector: SensorSelector;
  cursor?: string | null;
}
