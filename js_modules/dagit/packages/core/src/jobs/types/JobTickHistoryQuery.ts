// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobSelector, JobType, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: JobTickHistoryQuery
// ====================================================

export interface JobTickHistoryQuery_jobStateOrError_JobState_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface JobTickHistoryQuery_jobStateOrError_JobState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobTickHistoryQuery_jobStateOrError_JobState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobTickHistoryQuery_jobStateOrError_JobState_ticks_error_cause | null;
}

export interface JobTickHistoryQuery_jobStateOrError_JobState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  originRunIds: string[];
  error: JobTickHistoryQuery_jobStateOrError_JobState_ticks_error | null;
}

export interface JobTickHistoryQuery_jobStateOrError_JobState {
  __typename: "JobState";
  id: string;
  jobType: JobType;
  nextTick: JobTickHistoryQuery_jobStateOrError_JobState_nextTick | null;
  ticks: JobTickHistoryQuery_jobStateOrError_JobState_ticks[];
}

export interface JobTickHistoryQuery_jobStateOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobTickHistoryQuery_jobStateOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobTickHistoryQuery_jobStateOrError_PythonError_cause | null;
}

export type JobTickHistoryQuery_jobStateOrError = JobTickHistoryQuery_jobStateOrError_JobState | JobTickHistoryQuery_jobStateOrError_PythonError;

export interface JobTickHistoryQuery {
  jobStateOrError: JobTickHistoryQuery_jobStateOrError;
}

export interface JobTickHistoryQueryVariables {
  jobSelector: JobSelector;
  dayRange?: number | null;
  limit?: number | null;
}
