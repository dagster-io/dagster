// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleSelector, ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleRootQuery
// ====================================================

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  runConfigYaml: string | null;
  partitionSet: ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition_partitionSet | null;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_tags[];
  pipeline: ScheduleRootQuery_scheduleOrError_RunningSchedule_runs_pipeline;
  status: PipelineRunStatus;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickSuccessData_run_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  pipeline: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickSuccessData_run_pipeline;
  status: PipelineRunStatus;
  runId: string;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickFailureData_error;
}

export type ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData = ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickSuccessData | ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData_ScheduleTickFailureData;

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList_tickSpecificData | null;
}

export interface ScheduleRootQuery_scheduleOrError_RunningSchedule {
  __typename: "RunningSchedule";
  runningScheduleCount: number;
  scheduleDefinition: ScheduleRootQuery_scheduleOrError_RunningSchedule_scheduleDefinition;
  ticks: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticks[];
  runsCount: number;
  runs: ScheduleRootQuery_scheduleOrError_RunningSchedule_runs[];
  stats: ScheduleRootQuery_scheduleOrError_RunningSchedule_stats;
  ticksCount: number;
  status: ScheduleStatus;
  ticksList: ScheduleRootQuery_scheduleOrError_RunningSchedule_ticksList[];
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
  scheduleSelector: ScheduleSelector;
  limit: number;
  ticksLimit: number;
}
