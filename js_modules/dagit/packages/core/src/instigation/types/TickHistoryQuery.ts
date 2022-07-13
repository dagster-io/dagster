/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationSelector, InstigationTickStatus, InstigationType, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: TickHistoryQuery
// ====================================================

export interface TickHistoryQuery_instigationStateOrError_InstigationState_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState_ticks_runs {
  __typename: "Run";
  id: string;
  status: RunStatus;
  runId: string;
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error_causes[];
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  cursor: string | null;
  skipReason: string | null;
  runIds: string[];
  runs: TickHistoryQuery_instigationStateOrError_InstigationState_ticks_runs[];
  originRunIds: string[];
  error: TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error | null;
  runKeys: string[];
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState {
  __typename: "InstigationState";
  id: string;
  instigationType: InstigationType;
  nextTick: TickHistoryQuery_instigationStateOrError_InstigationState_nextTick | null;
  ticks: TickHistoryQuery_instigationStateOrError_InstigationState_ticks[];
}

export interface TickHistoryQuery_instigationStateOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface TickHistoryQuery_instigationStateOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: TickHistoryQuery_instigationStateOrError_PythonError_causes[];
}

export type TickHistoryQuery_instigationStateOrError = TickHistoryQuery_instigationStateOrError_InstigationState | TickHistoryQuery_instigationStateOrError_PythonError;

export interface TickHistoryQuery {
  instigationStateOrError: TickHistoryQuery_instigationStateOrError;
}

export interface TickHistoryQueryVariables {
  instigationSelector: InstigationSelector;
  dayRange?: number | null;
  limit?: number | null;
  cursor?: string | null;
  statuses?: InstigationTickStatus[] | null;
}
