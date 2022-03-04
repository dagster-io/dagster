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

export interface SetSensorCursorMutation_setSensorCursor_PythonError {
  __typename: "PythonError";
  message: string;
  className: string | null;
  stack: string[];
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
  status: InstigationStatus;
  typeSpecificData: SetSensorCursorMutation_setSensorCursor_Sensor_sensorState_typeSpecificData | null;
}

export interface SetSensorCursorMutation_setSensorCursor_Sensor {
  __typename: "Sensor";
  id: string;
  sensorState: SetSensorCursorMutation_setSensorCursor_Sensor_sensorState;
}

export type SetSensorCursorMutation_setSensorCursor = SetSensorCursorMutation_setSensorCursor_SensorNotFoundError | SetSensorCursorMutation_setSensorCursor_PythonError | SetSensorCursorMutation_setSensorCursor_Sensor;

export interface SetSensorCursorMutation {
  setSensorCursor: SetSensorCursorMutation_setSensorCursor;
}

export interface SetSensorCursorMutationVariables {
  sensorSelector: SensorSelector;
  cursor?: string | null;
}
