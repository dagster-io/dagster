/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleFragment
// ====================================================

export interface ScheduleFragment_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
}

export interface ScheduleFragment_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface ScheduleFragment_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type ScheduleFragment_scheduleState_typeSpecificData = ScheduleFragment_scheduleState_typeSpecificData_SensorData | ScheduleFragment_scheduleState_typeSpecificData_ScheduleData;

export interface ScheduleFragment_scheduleState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface ScheduleFragment_scheduleState_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleFragment_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: ScheduleFragment_scheduleState_ticks_error_causes[];
}

export interface ScheduleFragment_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: ScheduleFragment_scheduleState_ticks_error | null;
}

export interface ScheduleFragment_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
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
