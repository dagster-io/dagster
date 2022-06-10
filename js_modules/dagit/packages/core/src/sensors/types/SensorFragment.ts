/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: SensorFragment
// ====================================================

export interface SensorFragment_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface SensorFragment_sensorState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface SensorFragment_sensorState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type SensorFragment_sensorState_typeSpecificData = SensorFragment_sensorState_typeSpecificData_SensorData | SensorFragment_sensorState_typeSpecificData_ScheduleData;

export interface SensorFragment_sensorState_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SensorFragment_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorFragment_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorFragment_sensorState_ticks_error_cause | null;
}

export interface SensorFragment_sensorState_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: SensorFragment_sensorState_ticks_error | null;
}

export interface SensorFragment_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: SensorFragment_sensorState_typeSpecificData | null;
  runs: SensorFragment_sensorState_runs[];
  ticks: SensorFragment_sensorState_ticks[];
  runningCount: number;
}

export interface SensorFragment_targets {
  __typename: "Target";
  pipelineName: string;
  solidSelection: string[] | null;
  mode: string;
}

export interface SensorFragment_metadata_assetKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface SensorFragment_metadata {
  __typename: "SensorMetadata";
  assetKeys: SensorFragment_metadata_assetKeys[] | null;
}

export interface SensorFragment {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  description: string | null;
  minIntervalSeconds: number;
  nextTick: SensorFragment_nextTick | null;
  sensorState: SensorFragment_sensorState;
  targets: SensorFragment_targets[] | null;
  metadata: SensorFragment_metadata;
}
