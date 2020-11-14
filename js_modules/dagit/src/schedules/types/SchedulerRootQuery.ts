// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulerRootQuery
// ====================================================

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData = SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: JobTickStatus;
  timestamp: number;
  tickSpecificData: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks_tickSpecificData | null;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_ticks[];
  runsCount: number;
  runs: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_futureTicks {
  __typename: "ScheduleFutureTicks";
  results: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_futureTicks_results[];
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions {
  __typename: "ScheduleDefinition";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_partitionSet | null;
  scheduleState: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_scheduleState | null;
  futureTicks: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions_futureTicks;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin_repositoryLocationMetadata[];
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  scheduleDefinitions: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_scheduleDefinitions[];
  origin: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin;
  location: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes_location;
}

export interface SchedulerRootQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: SchedulerRootQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface SchedulerRootQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_repositoriesOrError_PythonError_cause | null;
}

export type SchedulerRootQuery_repositoriesOrError = SchedulerRootQuery_repositoriesOrError_RepositoryConnection | SchedulerRootQuery_repositoriesOrError_PythonError;

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

export interface SchedulerRootQuery_unLoadableScheduleStates_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData = SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickSuccessData | SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData_ScheduleTickFailureData;

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: JobTickStatus;
  timestamp: number;
  tickSpecificData: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks_tickSpecificData | null;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_ticks[];
  runsCount: number;
  runs: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates {
  __typename: "ScheduleStates";
  results: SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates_results[];
}

export interface SchedulerRootQuery_unLoadableScheduleStates_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_unLoadableScheduleStates_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_unLoadableScheduleStates_PythonError_cause | null;
}

export type SchedulerRootQuery_unLoadableScheduleStates = SchedulerRootQuery_unLoadableScheduleStates_RepositoryNotFoundError | SchedulerRootQuery_unLoadableScheduleStates_ScheduleStates | SchedulerRootQuery_unLoadableScheduleStates_PythonError;

export interface SchedulerRootQuery {
  repositoriesOrError: SchedulerRootQuery_repositoriesOrError;
  scheduler: SchedulerRootQuery_scheduler;
  unLoadableScheduleStates: SchedulerRootQuery_unLoadableScheduleStates;
}
