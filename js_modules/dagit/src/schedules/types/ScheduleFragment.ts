// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PartitionRunStatus, JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleFragment
// ====================================================

export interface ScheduleFragment_partitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
}

export interface ScheduleFragment_partitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
  status: PartitionRunStatus;
}

export interface ScheduleFragment_partitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: ScheduleFragment_partitionSet_partitionsOrError_Partitions_results[];
}

export type ScheduleFragment_partitionSet_partitionsOrError = ScheduleFragment_partitionSet_partitionsOrError_PythonError | ScheduleFragment_partitionSet_partitionsOrError_Partitions;

export interface ScheduleFragment_partitionSet {
  __typename: "PartitionSet";
  name: string;
  partitionsOrError: ScheduleFragment_partitionSet_partitionsOrError;
}

export interface ScheduleFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduleFragment_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduleFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface ScheduleFragment_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface ScheduleFragment_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type ScheduleFragment_scheduleState_jobSpecificData = ScheduleFragment_scheduleState_jobSpecificData_SensorJobData | ScheduleFragment_scheduleState_jobSpecificData_ScheduleJobData;

export interface ScheduleFragment_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface ScheduleFragment_scheduleState_ticks_runs {
  __typename: "PipelineRun";
  id: string;
}

export interface ScheduleFragment_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleFragment_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleFragment_scheduleState_ticks_error_cause | null;
}

export interface ScheduleFragment_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runs: ScheduleFragment_scheduleState_ticks_runs[];
  error: ScheduleFragment_scheduleState_ticks_error | null;
}

export interface ScheduleFragment_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: ScheduleFragment_scheduleState_repositoryOrigin;
  jobSpecificData: ScheduleFragment_scheduleState_jobSpecificData | null;
  runs: ScheduleFragment_scheduleState_runs[];
  ticks: ScheduleFragment_scheduleState_ticks[];
  runningCount: number;
}

export interface ScheduleFragment_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface ScheduleFragment_futureTicks {
  __typename: "FutureJobTicks";
  results: ScheduleFragment_futureTicks_results[];
}

export interface ScheduleFragment {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: ScheduleFragment_partitionSet | null;
  scheduleState: ScheduleFragment_scheduleState;
  futureTicks: ScheduleFragment_futureTicks;
}
