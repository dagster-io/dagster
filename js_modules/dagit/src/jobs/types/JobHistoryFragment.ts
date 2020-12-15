// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: JobHistoryFragment
// ====================================================

export interface JobHistoryFragment_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobHistoryFragment_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobHistoryFragment_ticks_error_cause | null;
}

export interface JobHistoryFragment_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: JobHistoryFragment_ticks_error | null;
}

export interface JobHistoryFragment {
  __typename: "JobState";
  id: string;
  ticks: JobHistoryFragment_ticks[];
}
