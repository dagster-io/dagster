// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSchedule
// ====================================================

export interface StopSchedule_stopRunningSchedule_ScheduleStateResult_scheduleState {
  __typename: "ScheduleState";
  id: string;
  runningScheduleCount: number;
  status: ScheduleStatus;
}

export interface StopSchedule_stopRunningSchedule_ScheduleStateResult {
  __typename: "ScheduleStateResult";
  scheduleState: StopSchedule_stopRunningSchedule_ScheduleStateResult_scheduleState;
}

export interface StopSchedule_stopRunningSchedule_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type StopSchedule_stopRunningSchedule = StopSchedule_stopRunningSchedule_ScheduleStateResult | StopSchedule_stopRunningSchedule_PythonError;

export interface StopSchedule {
  stopRunningSchedule: StopSchedule_stopRunningSchedule;
}

export interface StopScheduleVariables {
  scheduleOriginId: string;
}
