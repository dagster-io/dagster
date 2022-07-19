/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartSchedule
// ====================================================

export interface StartSchedule_startSchedule_UnauthorizedError {
  __typename: "UnauthorizedError";
}

export interface StartSchedule_startSchedule_ScheduleStateResult_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  runningCount: number;
}

export interface StartSchedule_startSchedule_ScheduleStateResult {
  __typename: "ScheduleStateResult";
  scheduleState: StartSchedule_startSchedule_ScheduleStateResult_scheduleState;
}

export interface StartSchedule_startSchedule_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface StartSchedule_startSchedule_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: StartSchedule_startSchedule_PythonError_causes[];
}

export type StartSchedule_startSchedule = StartSchedule_startSchedule_UnauthorizedError | StartSchedule_startSchedule_ScheduleStateResult | StartSchedule_startSchedule_PythonError;

export interface StartSchedule {
  startSchedule: StartSchedule_startSchedule;
}

export interface StartScheduleVariables {
  scheduleSelector: ScheduleSelector;
}
