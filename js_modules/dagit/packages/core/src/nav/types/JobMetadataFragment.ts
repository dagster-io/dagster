/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: JobMetadataFragment
// ====================================================

export interface JobMetadataFragment_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface JobMetadataFragment_schedules {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  scheduleState: JobMetadataFragment_schedules_scheduleState;
}

export interface JobMetadataFragment_sensors_targets {
  __typename: "Target";
  pipelineName: string;
  mode: string;
}

export interface JobMetadataFragment_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface JobMetadataFragment_sensors {
  __typename: "Sensor";
  id: string;
  targets: JobMetadataFragment_sensors_targets[] | null;
  jobOriginId: string;
  name: string;
  sensorState: JobMetadataFragment_sensors_sensorState;
}

export interface JobMetadataFragment {
  __typename: "Pipeline";
  id: string;
  isJob: boolean;
  name: string;
  schedules: JobMetadataFragment_schedules[];
  sensors: JobMetadataFragment_sensors[];
}
