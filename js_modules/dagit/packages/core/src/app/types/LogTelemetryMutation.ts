/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: LogTelemetryMutation
// ====================================================

export interface LogTelemetryMutation_logTelemetry_LogTelemetrySuccess {
  __typename: "LogTelemetrySuccess";
  action: string;
}

export interface LogTelemetryMutation_logTelemetry_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogTelemetryMutation_logTelemetry_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LogTelemetryMutation_logTelemetry_PythonError_causes[];
}

export type LogTelemetryMutation_logTelemetry = LogTelemetryMutation_logTelemetry_LogTelemetrySuccess | LogTelemetryMutation_logTelemetry_PythonError;

export interface LogTelemetryMutation {
  logTelemetry: LogTelemetryMutation_logTelemetry;
}

export interface LogTelemetryMutationVariables {
  action: string;
  metadata: string;
  clientTime: string;
}
