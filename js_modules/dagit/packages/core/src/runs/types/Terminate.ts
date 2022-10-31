/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { TerminateRunPolicy } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: Terminate
// ====================================================

export interface Terminate_terminatePipelineExecution_TerminateRunFailure {
  __typename: "TerminateRunFailure";
  message: string;
}

export interface Terminate_terminatePipelineExecution_RunNotFoundError {
  __typename: "RunNotFoundError";
  message: string;
}

export interface Terminate_terminatePipelineExecution_TerminateRunSuccess_run {
  __typename: "Run";
  id: string;
  runId: string;
  canTerminate: boolean;
}

export interface Terminate_terminatePipelineExecution_TerminateRunSuccess {
  __typename: "TerminateRunSuccess";
  run: Terminate_terminatePipelineExecution_TerminateRunSuccess_run;
}

export interface Terminate_terminatePipelineExecution_UnauthorizedError {
  __typename: "UnauthorizedError";
  message: string;
}

export interface Terminate_terminatePipelineExecution_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface Terminate_terminatePipelineExecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: Terminate_terminatePipelineExecution_PythonError_causes[];
}

export type Terminate_terminatePipelineExecution = Terminate_terminatePipelineExecution_TerminateRunFailure | Terminate_terminatePipelineExecution_RunNotFoundError | Terminate_terminatePipelineExecution_TerminateRunSuccess | Terminate_terminatePipelineExecution_UnauthorizedError | Terminate_terminatePipelineExecution_PythonError;

export interface Terminate {
  terminatePipelineExecution: Terminate_terminatePipelineExecution;
}

export interface TerminateVariables {
  runId: string;
  terminatePolicy?: TerminateRunPolicy | null;
}
