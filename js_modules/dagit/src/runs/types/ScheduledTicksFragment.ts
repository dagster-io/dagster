// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, JobType, JobStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduledTicksFragment
// ====================================================

export interface ScheduledTicksFragment_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError = ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError | ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData = ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData | ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData;

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause | null;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin;
  jobSpecificData: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData | null;
  runs: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureJobTicks";
  results: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: ScheduledTicksFragment_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduledTicksFragment_RepositoryConnection_nodes_origin_repositoryLocationMetadata[];
}

export interface ScheduledTicksFragment_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: ScheduledTicksFragment_RepositoryConnection_nodes_location;
  schedules: ScheduledTicksFragment_RepositoryConnection_nodes_schedules[];
  origin: ScheduledTicksFragment_RepositoryConnection_nodes_origin;
}

export interface ScheduledTicksFragment_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: ScheduledTicksFragment_RepositoryConnection_nodes[];
}

export interface ScheduledTicksFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduledTicksFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduledTicksFragment_PythonError_cause | null;
}

export type ScheduledTicksFragment = ScheduledTicksFragment_RepositoryConnection | ScheduledTicksFragment_PythonError;
