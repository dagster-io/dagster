/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunDetailsTestQuery
// ====================================================

export interface RunDetailsTestQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface RunDetailsTestQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  endTime: number | null;
  startTime: number | null;
  status: RunStatus;
}

export type RunDetailsTestQuery_pipelineRunOrError = RunDetailsTestQuery_pipelineRunOrError_RunNotFoundError | RunDetailsTestQuery_pipelineRunOrError_Run;

export interface RunDetailsTestQuery {
  pipelineRunOrError: RunDetailsTestQuery_pipelineRunOrError;
}
