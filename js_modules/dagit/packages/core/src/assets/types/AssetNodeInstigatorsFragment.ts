/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetNodeInstigatorsFragment
// ====================================================

export interface AssetNodeInstigatorsFragment_jobs_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface AssetNodeInstigatorsFragment_jobs_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  scheduleState: AssetNodeInstigatorsFragment_jobs_schedules_scheduleState;
}

export interface AssetNodeInstigatorsFragment_jobs_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface AssetNodeInstigatorsFragment_jobs_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  sensorState: AssetNodeInstigatorsFragment_jobs_sensors_sensorState;
}

export interface AssetNodeInstigatorsFragment_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
  schedules: AssetNodeInstigatorsFragment_jobs_schedules[];
  sensors: AssetNodeInstigatorsFragment_jobs_sensors[];
}

export interface AssetNodeInstigatorsFragment {
  __typename: "AssetNode";
  id: string;
  jobs: AssetNodeInstigatorsFragment_jobs[];
}
