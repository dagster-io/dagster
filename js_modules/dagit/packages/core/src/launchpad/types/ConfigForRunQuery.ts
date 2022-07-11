/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigForRunQuery
// ====================================================

export interface ConfigForRunQuery_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError";
}

export interface ConfigForRunQuery_runOrError_Run {
  __typename: "Run";
  id: string;
  mode: string;
  runConfigYaml: string;
  solidSelection: string[] | null;
}

export interface ConfigForRunQuery_runOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ConfigForRunQuery_runOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: ConfigForRunQuery_runOrError_PythonError_causes[];
}

export type ConfigForRunQuery_runOrError = ConfigForRunQuery_runOrError_RunNotFoundError | ConfigForRunQuery_runOrError_Run | ConfigForRunQuery_runOrError_PythonError;

export interface ConfigForRunQuery {
  runOrError: ConfigForRunQuery_runOrError;
}

export interface ConfigForRunQueryVariables {
  runId: string;
}
