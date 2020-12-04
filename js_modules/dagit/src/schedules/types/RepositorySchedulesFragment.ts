// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobTickStatus, PipelineRunStatus, ScheduleStatus, JobType, JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RepositorySchedulesFragment
// ====================================================

export interface RepositorySchedulesFragment_scheduleDefinitions_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData = RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: JobTickStatus;
  timestamp: number;
  tickSpecificData: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks_tickSpecificData | null;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_ticks[];
  runsCount: number;
  runs: RepositorySchedulesFragment_scheduleDefinitions_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface RepositorySchedulesFragment_scheduleDefinitions_futureTicks {
  __typename: "ScheduleFutureTicks";
  results: RepositorySchedulesFragment_scheduleDefinitions_futureTicks_results[];
}

export interface RepositorySchedulesFragment_scheduleDefinitions {
  __typename: "ScheduleDefinition";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: RepositorySchedulesFragment_scheduleDefinitions_partitionSet | null;
  scheduleState: RepositorySchedulesFragment_scheduleDefinitions_scheduleState | null;
  futureTicks: RepositorySchedulesFragment_scheduleDefinitions_futureTicks;
}

export interface RepositorySchedulesFragment_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositorySchedulesFragment_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: RepositorySchedulesFragment_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface RepositorySchedulesFragment_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface RepositorySchedulesFragment_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type RepositorySchedulesFragment_sensors_sensorState_jobSpecificData = RepositorySchedulesFragment_sensors_sensorState_jobSpecificData_SensorJobData | RepositorySchedulesFragment_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface RepositorySchedulesFragment_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface RepositorySchedulesFragment_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface RepositorySchedulesFragment_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: RepositorySchedulesFragment_sensors_sensorState_repositoryOrigin;
  jobSpecificData: RepositorySchedulesFragment_sensors_sensorState_jobSpecificData | null;
  runs: RepositorySchedulesFragment_sensors_sensorState_runs[];
  runsCount: number;
  ticks: RepositorySchedulesFragment_sensors_sensorState_ticks[];
}

export interface RepositorySchedulesFragment_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  sensorState: RepositorySchedulesFragment_sensors_sensorState;
}

export interface RepositorySchedulesFragment_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositorySchedulesFragment_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: RepositorySchedulesFragment_origin_repositoryLocationMetadata[];
}

export interface RepositorySchedulesFragment_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RepositorySchedulesFragment {
  __typename: "Repository";
  name: string;
  id: string;
  scheduleDefinitions: RepositorySchedulesFragment_scheduleDefinitions[];
  sensors: RepositorySchedulesFragment_sensors[];
  origin: RepositorySchedulesFragment_origin;
  location: RepositorySchedulesFragment_location;
}
