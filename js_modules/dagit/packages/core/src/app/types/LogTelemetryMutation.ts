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

export interface LogTelemetryMutation_logTelemetry_PythonError_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogTelemetryMutation_logTelemetry_PythonError_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: LogTelemetryMutation_logTelemetry_PythonError_errorChain_error;
}

export interface LogTelemetryMutation_logTelemetry_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: LogTelemetryMutation_logTelemetry_PythonError_errorChain[];
}

export type LogTelemetryMutation_logTelemetry = LogTelemetryMutation_logTelemetry_LogTelemetrySuccess | LogTelemetryMutation_logTelemetry_PythonError;

export interface LogTelemetryMutation {
  logTelemetry: LogTelemetryMutation_logTelemetry;
}

export interface LogTelemetryMutationVariables {
  action: string;
  metadata: string;
  clientTime: string;
  clientId: string;
}
