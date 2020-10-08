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

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin = ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_PythonRepositoryOrigin | ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin_GrpcRepositoryOrigin;

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData = ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks_tickSpecificData | null;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_ticks[];
  runsCount: number;
  runs: ScheduleRootQuery_scheduleDefinitionOrError_ScheduleDefinition_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
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
}
