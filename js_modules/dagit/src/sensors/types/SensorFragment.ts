// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: SensorFragment
// ====================================================

export interface SensorFragment_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SensorFragment_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SensorFragment_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SensorFragment_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface SensorFragment_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type SensorFragment_sensorState_jobSpecificData = SensorFragment_sensorState_jobSpecificData_SensorJobData | SensorFragment_sensorState_jobSpecificData_ScheduleJobData;

export interface SensorFragment_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SensorFragment_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface SensorFragment_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: SensorFragment_sensorState_repositoryOrigin;
  jobSpecificData: SensorFragment_sensorState_jobSpecificData | null;
  runs: SensorFragment_sensorState_runs[];
  runsCount: number;
  ticks: SensorFragment_sensorState_ticks[];
}

export interface SensorFragment {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  sensorState: SensorFragment_sensorState;
}
