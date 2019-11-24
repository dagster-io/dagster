// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleAttemptStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleRootQuery
// ====================================================

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  executionParamsString: string;
  environmentConfigYaml: string;
  cronSchedule: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts {
  __typename: "ScheduleAttempt";
  time: number;
  jsonResult: string;
  status: ScheduleAttemptStatus;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_stats {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_pipeline;
  status: PipelineRunStatus;
  stats: ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_stats;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_attemptList {
  __typename: "ScheduleAttempt";
  time: number;
  jsonResult: string;
  status: ScheduleAttemptStatus;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule {
  __typename: "RunningSchedule";
  id: string;
  scheduleDefinition: ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition;
  logsPath: string;
  runsCount: number;
  attempts: ScheduleRootQuery_scheduleOrError_RunningSchedule_attempts[];
  runs: ScheduleRootQuery_scheduleOrError_RunningSchedule_runs[];
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
