/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationSelector, InstigationType, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: TickHistoryQuery
// ====================================================

export interface TickHistoryQuery_instigationStateOrError_InstigationState_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error_cause | null;
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  originRunIds: string[];
  error: TickHistoryQuery_instigationStateOrError_InstigationState_ticks_error | null;
}

export interface TickHistoryQuery_instigationStateOrError_InstigationState {
  __typename: "InstigationState";
  id: string;
  instigationType: InstigationType;
  nextTick: TickHistoryQuery_instigationStateOrError_InstigationState_nextTick | null;
  ticks: TickHistoryQuery_instigationStateOrError_InstigationState_ticks[];
}

export interface TickHistoryQuery_instigationStateOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface TickHistoryQuery_instigationStateOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: TickHistoryQuery_instigationStateOrError_PythonError_cause | null;
}

export type TickHistoryQuery_instigationStateOrError = TickHistoryQuery_instigationStateOrError_InstigationState | TickHistoryQuery_instigationStateOrError_PythonError;

export interface TickHistoryQuery {
  instigationStateOrError: TickHistoryQuery_instigationStateOrError;
}

export interface TickHistoryQueryVariables {
  instigationSelector: InstigationSelector;
  dayRange?: number | null;
  limit?: number | null;
}
