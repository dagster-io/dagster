// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_schedules_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  runConfigYaml: string | null;
}

export interface SchedulesRootQuery_schedules_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface SchedulesRootQuery_schedules_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_schedules_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface SchedulesRootQuery_schedules_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: SchedulesRootQuery_schedules_runs_tags[];
  pipeline: SchedulesRootQuery_schedules_runs_pipeline;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_schedules_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface SchedulesRootQuery_schedules {
  __typename: "RunningSchedule";
  runningScheduleCount: number;
  scheduleDefinition: SchedulesRootQuery_schedules_scheduleDefinition;
  ticks: SchedulesRootQuery_schedules_ticks[];
  runsCount: number;
  runs: SchedulesRootQuery_schedules_runs[];
  stats: SchedulesRootQuery_schedules_stats;
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulesRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
}

export interface SchedulesRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulesRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type SchedulesRootQuery_scheduler = SchedulesRootQuery_scheduler_Scheduler | SchedulesRootQuery_scheduler_SchedulerNotDefinedError | SchedulesRootQuery_scheduler_PythonError;

export interface SchedulesRootQuery {
  schedules: SchedulesRootQuery_schedules[];
  scheduler: SchedulesRootQuery_scheduler;
}

export interface SchedulesRootQueryVariables {
  limit: number;
}
