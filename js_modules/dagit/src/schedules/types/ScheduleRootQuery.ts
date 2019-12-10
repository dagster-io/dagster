// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, ScheduleAttemptStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleRootQuery
// ====================================================

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSubset: (string | null)[] | null;
  mode: string;
  environmentConfigYaml: string | null;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts_run_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts_run_pipeline;
  status: PipelineRunStatus;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts {
  __typename: "ScheduleAttempt";
  run: ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts_run | null;
  time: number;
  jsonResult: string;
  status: ScheduleAttemptStatus;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList_run {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList {
  __typename: "ScheduleAttempt";
  time: number;
  jsonResult: string;
  status: ScheduleAttemptStatus;
  run: ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList_run | null;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule {
  __typename: "RunningSchedule";
  scheduleDefinition: ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition;
  logsPath: string;
  attempts: ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts[];
  attemptsCount: number;
  status: ScheduleStatus;
  attemptList: ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList[];
}

export interface ScheduleRootQuery_scheduleOrError_ScheduleNotFoundError {
  __typename: "ScheduleNotFoundError";
  message: string;
}

export interface ScheduleRootQuery_scheduleOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type ScheduleRootQuery_scheduleOrError = ScheduleRootQuery_scheduleOrError_RunningSchedule | ScheduleRootQuery_scheduleOrError_ScheduleNotFoundError | ScheduleRootQuery_scheduleOrError_PythonError;

export interface ScheduleRootQuery {
  scheduleOrError: ScheduleRootQuery_scheduleOrError;
}

export interface ScheduleRootQueryVariables {
  scheduleName: string;
  limit: number;
  attemptsLimit: number;
}
