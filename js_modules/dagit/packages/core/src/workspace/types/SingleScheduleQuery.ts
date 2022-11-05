/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector, InstigationTickStatus, RunStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SingleScheduleQuery
// ====================================================

export interface SingleScheduleQuery_scheduleOrError_ScheduleNotFoundError {
  __typename: "ScheduleNotFoundError" | "PythonError";
}

export interface SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_ticks_error_causes[];
}

export interface SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_ticks_error | null;
}

export interface SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SingleScheduleQuery_scheduleOrError_Schedule_scheduleState {
  __typename: "InstigationState";
  id: string;
  runningCount: number;
  ticks: SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_ticks[];
  runs: SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_runs[];
  nextTick: SingleScheduleQuery_scheduleOrError_Schedule_scheduleState_nextTick | null;
  selectorId: string;
  status: InstigationStatus;
}

export interface SingleScheduleQuery_scheduleOrError_Schedule_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface SingleScheduleQuery_scheduleOrError_Schedule {
  __typename: "Schedule";
  id: string;
  name: string;
  pipelineName: string;
  description: string | null;
  scheduleState: SingleScheduleQuery_scheduleOrError_Schedule_scheduleState;
  partitionSet: SingleScheduleQuery_scheduleOrError_Schedule_partitionSet | null;
  cronSchedule: string;
  executionTimezone: string | null;
}

export type SingleScheduleQuery_scheduleOrError = SingleScheduleQuery_scheduleOrError_ScheduleNotFoundError | SingleScheduleQuery_scheduleOrError_Schedule;

export interface SingleScheduleQuery {
  scheduleOrError: SingleScheduleQuery_scheduleOrError;
}

export interface SingleScheduleQueryVariables {
  selector: ScheduleSelector;
}
