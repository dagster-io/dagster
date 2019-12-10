// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, ScheduleAttemptStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleFragment
// ====================================================

export interface ScheduleFragment_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSubset: (string | null)[] | null;
  mode: string;
  environmentConfigYaml: string | null;
}

export interface ScheduleFragment_attempts_run_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface ScheduleFragment_attempts_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: ScheduleFragment_attempts_run_pipeline;
  status: PipelineRunStatus;
}

export interface ScheduleFragment_attempts {
  __typename: "ScheduleAttempt";
  run: ScheduleFragment_attempts_run | null;
  time: number;
  jsonResult: string;
  status: ScheduleAttemptStatus;
}

export interface ScheduleFragment {
  __typename: "RunningSchedule";
  scheduleDefinition: ScheduleFragment_scheduleDefinition;
  logsPath: string;
  attempts: ScheduleFragment_attempts[];
  attemptsCount: number;
  status: ScheduleStatus;
}
