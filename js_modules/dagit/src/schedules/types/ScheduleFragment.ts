// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleAttemptStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleFragment
// ====================================================

export interface ScheduleFragment_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  executionParamsString: string;
  environmentConfigYaml: string;
  cronSchedule: string;
}

export interface ScheduleFragment_attempts {
  __typename: "ScheduleAttempt";
  time: string;
  jsonResult: string;
  status: ScheduleAttemptStatus;
}

export interface ScheduleFragment_runs_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface ScheduleFragment_runs_stats {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
}

export interface ScheduleFragment_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: ScheduleFragment_runs_pipeline;
  status: PipelineRunStatus;
  stats: ScheduleFragment_runs_stats;
}

export interface ScheduleFragment {
  __typename: "RunningSchedule";
  id: string;
  scheduleDefinition: ScheduleFragment_scheduleDefinition;
  logsPath: string;
  runsCount: number;
  attempts: ScheduleFragment_attempts[];
  runs: ScheduleFragment_runs[];
  status: ScheduleStatus;
}
