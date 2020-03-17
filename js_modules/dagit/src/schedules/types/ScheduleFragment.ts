// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

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

export interface ScheduleFragment_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface ScheduleFragment_runs_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface ScheduleFragment_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: ScheduleFragment_runs_pipeline;
  status: PipelineRunStatus;
}

export interface ScheduleFragment_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface ScheduleFragment {
  __typename: "RunningSchedule";
  scheduleDefinition: ScheduleFragment_scheduleDefinition;
  logsPath: string;
  ticks: ScheduleFragment_ticks[];
  runsCount: number;
  runs: ScheduleFragment_runs[];
  stats: ScheduleFragment_stats;
  ticksCount: number;
  status: ScheduleStatus;
}
