// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleTickHistoryQuery
// ====================================================

export interface ScheduleTickHistoryQuery_scheduleOrError_ScheduleNotFoundError {
  __typename: "ScheduleNotFoundError" | "PythonError";
}

export interface ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState_ticks_error_cause | null;
}

export interface ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState_ticks_error | null;
}

export interface ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState {
  __typename: "JobState";
  id: string;
  ticks: ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState_ticks[];
}

export interface ScheduleTickHistoryQuery_scheduleOrError_Schedule {
  __typename: "Schedule";
  id: string;
  scheduleState: ScheduleTickHistoryQuery_scheduleOrError_Schedule_scheduleState;
}

export type ScheduleTickHistoryQuery_scheduleOrError = ScheduleTickHistoryQuery_scheduleOrError_ScheduleNotFoundError | ScheduleTickHistoryQuery_scheduleOrError_Schedule;

export interface ScheduleTickHistoryQuery {
  scheduleOrError: ScheduleTickHistoryQuery_scheduleOrError;
}

export interface ScheduleTickHistoryQueryVariables {
  scheduleSelector: ScheduleSelector;
}
