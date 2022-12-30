/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: StepSummaryForRunQuery
// ====================================================

export interface StepSummaryForRunQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface StepSummaryForRunQuery_pipelineRunOrError_Run_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  stepKey: string;
  status: StepEventStatus | null;
}

export interface StepSummaryForRunQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  status: RunStatus;
  stepStats: StepSummaryForRunQuery_pipelineRunOrError_Run_stepStats[];
}

export type StepSummaryForRunQuery_pipelineRunOrError = StepSummaryForRunQuery_pipelineRunOrError_RunNotFoundError | StepSummaryForRunQuery_pipelineRunOrError_Run;

export interface StepSummaryForRunQuery {
  pipelineRunOrError: StepSummaryForRunQuery_pipelineRunOrError;
}

export interface StepSummaryForRunQueryVariables {
  runId: string;
}
