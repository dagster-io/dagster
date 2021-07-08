// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { TerminatePipelinePolicy } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: Terminate
// ====================================================

export interface Terminate_terminatePipelineExecution_TerminatePipelineExecutionFailure {
  __typename: "TerminatePipelineExecutionFailure";
  message: string;
}

export interface Terminate_terminatePipelineExecution_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
  message: string;
}

export interface Terminate_terminatePipelineExecution_TerminatePipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  canTerminate: boolean;
}

export interface Terminate_terminatePipelineExecution_TerminatePipelineExecutionSuccess {
  __typename: "TerminatePipelineExecutionSuccess";
  run: Terminate_terminatePipelineExecution_TerminatePipelineExecutionSuccess_run;
}

export interface Terminate_terminatePipelineExecution_UnauthorizedError {
  __typename: "UnauthorizedError";
  message: string;
}

export interface Terminate_terminatePipelineExecution_PythonError {
  __typename: "PythonError";
  message: string;
}

export type Terminate_terminatePipelineExecution = Terminate_terminatePipelineExecution_TerminatePipelineExecutionFailure | Terminate_terminatePipelineExecution_PipelineRunNotFoundError | Terminate_terminatePipelineExecution_TerminatePipelineExecutionSuccess | Terminate_terminatePipelineExecution_UnauthorizedError | Terminate_terminatePipelineExecution_PythonError;

export interface Terminate {
  terminatePipelineExecution: Terminate_terminatePipelineExecution;
}

export interface TerminateVariables {
  runId: string;
  terminatePolicy?: TerminatePipelinePolicy | null;
}
