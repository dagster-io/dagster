/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSchedule
// ====================================================

export interface StopSchedule_stopRunningSchedule_UnauthorizedError {
  __typename: "UnauthorizedError";
}

export interface StopSchedule_stopRunningSchedule_ScheduleStateResult_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
  runningCount: number;
}

export interface StopSchedule_stopRunningSchedule_ScheduleStateResult {
  __typename: "ScheduleStateResult";
  scheduleState: StopSchedule_stopRunningSchedule_ScheduleStateResult_scheduleState;
}

export interface StopSchedule_stopRunningSchedule_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface StopSchedule_stopRunningSchedule_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: StopSchedule_stopRunningSchedule_PythonError_causes[];
}

export type StopSchedule_stopRunningSchedule = StopSchedule_stopRunningSchedule_UnauthorizedError | StopSchedule_stopRunningSchedule_ScheduleStateResult | StopSchedule_stopRunningSchedule_PythonError;

export interface StopSchedule {
  stopRunningSchedule: StopSchedule_stopRunningSchedule;
}

export interface StopScheduleVariables {
  scheduleOriginId: string;
  scheduleSelectorId: string;
}
