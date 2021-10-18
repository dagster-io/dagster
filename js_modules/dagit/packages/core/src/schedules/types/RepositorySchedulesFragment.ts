// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, PipelineRunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RepositorySchedulesFragment
// ====================================================

export interface RepositorySchedulesFragment_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RepositorySchedulesFragment_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface RepositorySchedulesFragment_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositorySchedulesFragment_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: RepositorySchedulesFragment_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface RepositorySchedulesFragment_schedules_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
}

export interface RepositorySchedulesFragment_schedules_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type RepositorySchedulesFragment_schedules_scheduleState_typeSpecificData = RepositorySchedulesFragment_schedules_scheduleState_typeSpecificData_SensorData | RepositorySchedulesFragment_schedules_scheduleState_typeSpecificData_ScheduleData;

export interface RepositorySchedulesFragment_schedules_scheduleState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface RepositorySchedulesFragment_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RepositorySchedulesFragment_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RepositorySchedulesFragment_schedules_scheduleState_ticks_error_cause | null;
}

export interface RepositorySchedulesFragment_schedules_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: RepositorySchedulesFragment_schedules_scheduleState_ticks_error | null;
}

export interface RepositorySchedulesFragment_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryOrigin: RepositorySchedulesFragment_schedules_scheduleState_repositoryOrigin;
  typeSpecificData: RepositorySchedulesFragment_schedules_scheduleState_typeSpecificData | null;
  runs: RepositorySchedulesFragment_schedules_scheduleState_runs[];
  ticks: RepositorySchedulesFragment_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface RepositorySchedulesFragment_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface RepositorySchedulesFragment_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: RepositorySchedulesFragment_schedules_futureTicks_results[];
}

export interface RepositorySchedulesFragment_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  description: string | null;
  partitionSet: RepositorySchedulesFragment_schedules_partitionSet | null;
  scheduleState: RepositorySchedulesFragment_schedules_scheduleState;
  futureTicks: RepositorySchedulesFragment_schedules_futureTicks;
}

export interface RepositorySchedulesFragment_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositorySchedulesFragment {
  __typename: "Repository";
  name: string;
  id: string;
  location: RepositorySchedulesFragment_location;
  schedules: RepositorySchedulesFragment_schedules[];
  displayMetadata: RepositorySchedulesFragment_displayMetadata[];
}
