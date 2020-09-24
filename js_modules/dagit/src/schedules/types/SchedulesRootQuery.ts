// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector, ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulesRootQuery_repositoryOrError_Repository_origin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_origin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: SchedulesRootQuery_repositoryOrError_Repository_origin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_origin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: SchedulesRootQuery_repositoryOrError_Repository_origin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_origin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type SchedulesRootQuery_repositoryOrError_Repository_origin = SchedulesRootQuery_repositoryOrError_Repository_origin_PythonRepositoryOrigin | SchedulesRootQuery_repositoryOrError_Repository_origin_GrpcRepositoryOrigin;

export interface SchedulesRootQuery_repositoryOrError_Repository_location {
  __typename: "RepositoryLocation";
  name: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository {
  __typename: "Repository";
  name: string;
  id: string;
  origin: SchedulesRootQuery_repositoryOrError_Repository_origin;
  location: SchedulesRootQuery_repositoryOrError_Repository_location;
}

export interface SchedulesRootQuery_repositoryOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_repositoryOrError_PythonError_cause | null;
}

export type SchedulesRootQuery_repositoryOrError = SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError | SchedulesRootQuery_repositoryOrError_Repository | SchedulesRootQuery_repositoryOrError_PythonError;

export interface SchedulesRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface SchedulesRootQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_scheduler_PythonError_cause | null;
}

export type SchedulesRootQuery_scheduler = SchedulesRootQuery_scheduler_SchedulerNotDefinedError | SchedulesRootQuery_scheduler_Scheduler | SchedulesRootQuery_scheduler_PythonError;

export interface SchedulesRootQuery_scheduleDefinitionsOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin = SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_PythonRepositoryOrigin | SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin_GrpcRepositoryOrigin;

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData = SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks_tickSpecificData | null;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_ticks[];
  runsCount: number;
  runs: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_partitionSet | null;
  scheduleState: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState | null;
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions {
  __typename: "ScheduleDefinitions";
  results: SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_scheduleDefinitionsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_scheduleDefinitionsOrError_PythonError_cause | null;
}

export type SchedulesRootQuery_scheduleDefinitionsOrError = SchedulesRootQuery_scheduleDefinitionsOrError_RepositoryNotFoundError | SchedulesRootQuery_scheduleDefinitionsOrError_ScheduleDefinitions | SchedulesRootQuery_scheduleDefinitionsOrError_PythonError;

export interface SchedulesRootQuery_scheduleStatesOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin = SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin | SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_GrpcRepositoryOrigin;

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData = SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData | SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData;

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData | null;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks[];
  runsCount: number;
  runs: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulesRootQuery_scheduleStatesOrError_ScheduleStates {
  __typename: "ScheduleStates";
  results: SchedulesRootQuery_scheduleStatesOrError_ScheduleStates_results[];
}

export interface SchedulesRootQuery_scheduleStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_scheduleStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_scheduleStatesOrError_PythonError_cause | null;
}

export type SchedulesRootQuery_scheduleStatesOrError = SchedulesRootQuery_scheduleStatesOrError_RepositoryNotFoundError | SchedulesRootQuery_scheduleStatesOrError_ScheduleStates | SchedulesRootQuery_scheduleStatesOrError_PythonError;

export interface SchedulesRootQuery {
  repositoryOrError: SchedulesRootQuery_repositoryOrError;
  scheduler: SchedulesRootQuery_scheduler;
  scheduleDefinitionsOrError: SchedulesRootQuery_scheduleDefinitionsOrError;
  scheduleStatesOrError: SchedulesRootQuery_scheduleStatesOrError;
}

export interface SchedulesRootQueryVariables {
  repositorySelector: RepositorySelector;
}
