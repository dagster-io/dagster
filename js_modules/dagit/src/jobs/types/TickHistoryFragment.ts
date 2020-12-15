// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: TickHistoryFragment
// ====================================================

export interface TickHistoryFragment_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface TickHistoryFragment_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: TickHistoryFragment_error_cause | null;
}

export interface TickHistoryFragment {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: TickHistoryFragment_error | null;
}
