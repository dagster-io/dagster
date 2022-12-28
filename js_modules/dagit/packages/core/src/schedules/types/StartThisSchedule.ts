/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartThisSchedule
// ====================================================

export interface StartThisSchedule_startSchedule_UnauthorizedError {
  __typename: "UnauthorizedError";
}

export interface StartThisSchedule_startSchedule_ScheduleStateResult_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  runningCount: number;
}

export interface StartThisSchedule_startSchedule_ScheduleStateResult {
  __typename: "ScheduleStateResult";
  scheduleState: StartThisSchedule_startSchedule_ScheduleStateResult_scheduleState;
}

export interface StartThisSchedule_startSchedule_PythonError_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface StartThisSchedule_startSchedule_PythonError_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: StartThisSchedule_startSchedule_PythonError_errorChain_error;
}

export interface StartThisSchedule_startSchedule_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: StartThisSchedule_startSchedule_PythonError_errorChain[];
}

export type StartThisSchedule_startSchedule = StartThisSchedule_startSchedule_UnauthorizedError | StartThisSchedule_startSchedule_ScheduleStateResult | StartThisSchedule_startSchedule_PythonError;

export interface StartThisSchedule {
  startSchedule: StartThisSchedule_startSchedule;
}

export interface StartThisScheduleVariables {
  scheduleSelector: ScheduleSelector;
}
