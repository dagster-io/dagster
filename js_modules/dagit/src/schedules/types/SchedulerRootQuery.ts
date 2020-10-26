// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulerRootQuery
// ====================================================

export interface SchedulerRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulerRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface SchedulerRootQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_scheduler_PythonError_cause | null;
}

export type SchedulerRootQuery_scheduler = SchedulerRootQuery_scheduler_SchedulerNotDefinedError | SchedulerRootQuery_scheduler_Scheduler | SchedulerRootQuery_scheduler_PythonError;

export interface SchedulerRootQuery_scheduleStatesOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin = SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_PythonRepositoryOrigin | SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin_GrpcRepositoryOrigin;

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData = SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData | SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData;

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks_tickSpecificData | null;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_ticks[];
  runsCount: number;
  runs: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulerRootQuery_scheduleStatesOrError_ScheduleStates {
  __typename: "ScheduleStates";
  results: SchedulerRootQuery_scheduleStatesOrError_ScheduleStates_results[];
}

export interface SchedulerRootQuery_scheduleStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_scheduleStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_scheduleStatesOrError_PythonError_cause | null;
}

export type SchedulerRootQuery_scheduleStatesOrError = SchedulerRootQuery_scheduleStatesOrError_RepositoryNotFoundError | SchedulerRootQuery_scheduleStatesOrError_ScheduleStates | SchedulerRootQuery_scheduleStatesOrError_PythonError;

export interface SchedulerRootQuery {
  scheduler: SchedulerRootQuery_scheduler;
  scheduleStatesOrError: SchedulerRootQuery_scheduleStatesOrError;
}
