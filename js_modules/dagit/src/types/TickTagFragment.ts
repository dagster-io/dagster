// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobTickStatus, PipelineRunStatus } from "./globalTypes";

// ====================================================
// GraphQL fragment: TickTagFragment
// ====================================================

export interface TickTagFragment_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface TickTagFragment_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface TickTagFragment_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: TickTagFragment_error_cause | null;
}

export interface TickTagFragment {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  runs: TickTagFragment_runs[];
  error: TickTagFragment_error | null;
}
