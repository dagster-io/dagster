// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleSelector, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartSchedule
// ====================================================

export interface StartSchedule_startSchedule_RunningScheduleResult_schedule_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
}

export interface StartSchedule_startSchedule_RunningScheduleResult_schedule {
  __typename: "RunningSchedule";
  runningScheduleCount: number;
  scheduleDefinition: StartSchedule_startSchedule_RunningScheduleResult_schedule_scheduleDefinition;
  status: ScheduleStatus;
}

export interface StartSchedule_startSchedule_RunningScheduleResult {
  __typename: "RunningScheduleResult";
  schedule: StartSchedule_startSchedule_RunningScheduleResult_schedule;
}

export interface StartSchedule_startSchedule_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StartSchedule_startSchedule = StartSchedule_startSchedule_RunningScheduleResult | StartSchedule_startSchedule_PythonError;

export interface StartSchedule {
  startSchedule: StartSchedule_startSchedule;
}

export interface StartScheduleVariables {
  scheduleSelector: ScheduleSelector;
}
