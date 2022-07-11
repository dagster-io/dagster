/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: InstigationStateFragment
// ====================================================

export interface InstigationStateFragment_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface InstigationStateFragment_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type InstigationStateFragment_typeSpecificData = InstigationStateFragment_typeSpecificData_SensorData | InstigationStateFragment_typeSpecificData_ScheduleData;

export interface InstigationStateFragment_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface InstigationStateFragment_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstigationStateFragment_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstigationStateFragment_ticks_error_causes[];
}

export interface InstigationStateFragment_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: InstigationStateFragment_ticks_error | null;
}

export interface InstigationStateFragment {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: InstigationStateFragment_typeSpecificData | null;
  runs: InstigationStateFragment_runs[];
  ticks: InstigationStateFragment_ticks[];
  runningCount: number;
}
