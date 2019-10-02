// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

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
  executionParamsString: string;
  cronSchedule: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_stats {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_pipeline;
  status: PipelineRunStatus;
  stats: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs_stats;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules {
  __typename: "RunningSchedule";
  scheduleId: string;
  scheduleDefinition: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_scheduleDefinition;
  logsPath: string;
  runs: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_runs[];
  status: ScheduleStatus;
}

export interface SchedulesRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  runningSchedules: SchedulesRootQuery_scheduler_Scheduler_runningSchedules[];
}

export type SchedulesRootQuery_scheduler = SchedulesRootQuery_scheduler_SchedulerNotDefinedError | SchedulesRootQuery_scheduler_Scheduler;

export interface SchedulesRootQuery {
  scheduler: SchedulesRootQuery_scheduler;
}
