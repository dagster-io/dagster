// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleSelector, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartSchedule
// ====================================================

export interface StartSchedule_startSchedule_ScheduleStateResult_scheduleState {
  __typename: "ScheduleState";
  id: string;
  runningScheduleCount: number;
  status: ScheduleStatus;
}

export interface StartSchedule_startSchedule_ScheduleStateResult {
  __typename: "ScheduleStateResult";
  scheduleState: StartSchedule_startSchedule_ScheduleStateResult_scheduleState;
}

export interface StartSchedule_startSchedule_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StartSchedule_startSchedule = StartSchedule_startSchedule_ScheduleStateResult | StartSchedule_startSchedule_PythonError;

export interface StartSchedule {
  startSchedule: StartSchedule_startSchedule;
}

export interface StartScheduleVariables {
  scheduleSelector: ScheduleSelector;
}
