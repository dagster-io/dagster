// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleSelector, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSchedule
// ====================================================

export interface StopSchedule_stopRunningSchedule_RunningScheduleResult_schedule_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
}

export interface StopSchedule_stopRunningSchedule_RunningScheduleResult_schedule {
  __typename: "RunningSchedule";
  runningScheduleCount: number;
  scheduleDefinition: StopSchedule_stopRunningSchedule_RunningScheduleResult_schedule_scheduleDefinition;
  status: ScheduleStatus;
}

export interface StopSchedule_stopRunningSchedule_RunningScheduleResult {
  __typename: "RunningScheduleResult";
  schedule: StopSchedule_stopRunningSchedule_RunningScheduleResult_schedule;
}

export interface StopSchedule_stopRunningSchedule_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StopSchedule_stopRunningSchedule = StopSchedule_stopRunningSchedule_RunningScheduleResult | StopSchedule_stopRunningSchedule_PythonError;

export interface StopSchedule {
  stopRunningSchedule: StopSchedule_stopRunningSchedule;
}

export interface StopScheduleVariables {
  scheduleSelector: ScheduleSelector;
}
