/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleTickConfigQuery
// ====================================================

export interface ScheduleTickConfigQuery_scheduleOrError_ScheduleNotFoundError {
  __typename: "ScheduleNotFoundError" | "PythonError";
}

export interface ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_runRequests_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_runRequests {
  __typename: "RunRequest";
  runKey: string | null;
  runConfigYaml: string;
  tags: ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_runRequests_tags[];
}

export interface ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_error_causes[];
}

export interface ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult {
  __typename: "TickEvaluation";
  runRequests: (ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_runRequests | null)[] | null;
  skipReason: string | null;
  error: ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult_error | null;
}

export interface ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick {
  __typename: "FutureInstigationTick";
  evaluationResult: ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick_evaluationResult | null;
}

export interface ScheduleTickConfigQuery_scheduleOrError_Schedule {
  __typename: "Schedule";
  id: string;
  futureTick: ScheduleTickConfigQuery_scheduleOrError_Schedule_futureTick;
}

export type ScheduleTickConfigQuery_scheduleOrError = ScheduleTickConfigQuery_scheduleOrError_ScheduleNotFoundError | ScheduleTickConfigQuery_scheduleOrError_Schedule;

export interface ScheduleTickConfigQuery {
  scheduleOrError: ScheduleTickConfigQuery_scheduleOrError;
}

export interface ScheduleTickConfigQueryVariables {
  scheduleSelector: ScheduleSelector;
  tickTimestamp: number;
}
