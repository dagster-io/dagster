// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSubset: (string | null)[] | null;
  mode: string;
  environmentConfigYaml: string | null;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_pipeline;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules {
  __typename: "RunningSchedule";
  scheduleDefinition: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_scheduleDefinition;
  logsPath: string;
  ticks: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_ticks[];
  runsCount: number;
  runs: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs[];
  stats: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_stats;
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulesRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  runningSchedules: SchedulesRootQuery_scheduler_Scheduler_runningSchedules[];
}

export interface SchedulesRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type SchedulesRootQuery_scheduler = SchedulesRootQuery_scheduler_SchedulerNotDefinedError | SchedulesRootQuery_scheduler_Scheduler | SchedulesRootQuery_scheduler_PythonError;

export interface SchedulesRootQuery {
  scheduler: SchedulesRootQuery_scheduler;
}

export interface SchedulesRootQueryVariables {
  limit: number;
}
