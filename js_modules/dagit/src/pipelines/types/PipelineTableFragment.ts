// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineTableFragment
// ====================================================

export interface PipelineTableFragment_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface PipelineTableFragment_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
}

export interface PipelineTableFragment_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
}

export interface PipelineTableFragment {
  __typename: "Pipeline";
  id: string;
  description: string | null;
  name: string;
  runs: PipelineTableFragment_runs[];
  schedules: PipelineTableFragment_schedules[];
  sensors: PipelineTableFragment_sensors[];
}
