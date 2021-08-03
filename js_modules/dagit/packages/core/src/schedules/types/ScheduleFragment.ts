// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, PipelineRunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleFragment
// ====================================================

export interface ScheduleFragment_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface ScheduleFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduleFragment_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduleFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface ScheduleFragment_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
}

export interface ScheduleFragment_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type ScheduleFragment_scheduleState_typeSpecificData = ScheduleFragment_scheduleState_typeSpecificData_SensorData | ScheduleFragment_scheduleState_typeSpecificData_ScheduleData;

export interface ScheduleFragment_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
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
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: ScheduleFragment_scheduleState_ticks_error | null;
}

export interface ScheduleFragment_scheduleState {
  __typename: "InstigationState";
  id: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryOrigin: ScheduleFragment_scheduleState_repositoryOrigin;
  typeSpecificData: ScheduleFragment_scheduleState_typeSpecificData | null;
  runs: ScheduleFragment_scheduleState_runs[];
  ticks: ScheduleFragment_scheduleState_ticks[];
  runningCount: number;
}

export interface ScheduleFragment_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface ScheduleFragment_futureTicks {
  __typename: "FutureInstigationTicks";
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
  description: string | null;
  partitionSet: ScheduleFragment_partitionSet | null;
  scheduleState: ScheduleFragment_scheduleState;
  futureTicks: ScheduleFragment_futureTicks;
}
