// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleSelector, ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ScheduleRootQuery
// ====================================================

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs_tags[];
  pipeline: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs_pipeline;
  status: PipelineRunStatus;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickSuccessData_run_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  pipeline: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickSuccessData_run_pipeline;
  status: PipelineRunStatus;
  runId: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickFailureData_error;
}

export type ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData = ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickSuccessData | ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData_ScheduleTickFailureData;

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList_tickSpecificData | null;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  runningScheduleCount: number;
  ticks: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks[];
  runsCount: number;
  runs: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs[];
  stats: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_stats;
  ticksCount: number;
  status: ScheduleStatus;
  ticksList: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticksList[];
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_partitionSet | null;
  scheduleState: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState | null;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinitionNotFoundError {
  __typename: "ScheduleDefinitionNotFoundError";
  message: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type ScheduleRootQuery_scheduleDefinitionOrError = ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition | ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinitionNotFoundError | ScheduleRootQuery_scheduleDefinitionOrError_PythonError;

export interface ScheduleRootQuery {
  scheduleDefinitionOrError: ScheduleRootQuery_scheduleDefinitionOrError;
}

export interface ScheduleRootQueryVariables {
  scheduleSelector: ScheduleSelector;
  limit: number;
  ticksLimit: number;
}
