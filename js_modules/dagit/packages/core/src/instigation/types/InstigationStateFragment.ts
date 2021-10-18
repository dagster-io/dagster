// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, PipelineRunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: InstigationStateFragment
// ====================================================

export interface InstigationStateFragment_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstigationStateFragment_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstigationStateFragment_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstigationStateFragment_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
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
  status: PipelineRunStatus;
}

export interface InstigationStateFragment_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstigationStateFragment_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstigationStateFragment_ticks_error_cause | null;
}

export interface InstigationStateFragment_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstigationStateFragment_ticks_error | null;
}

export interface InstigationStateFragment {
  __typename: "InstigationState";
  id: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryOrigin: InstigationStateFragment_repositoryOrigin;
  typeSpecificData: InstigationStateFragment_typeSpecificData | null;
  runs: InstigationStateFragment_runs[];
  ticks: InstigationStateFragment_ticks[];
  runningCount: number;
}
