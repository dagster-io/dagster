// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewScheduleFragment
// ====================================================

export interface OverviewScheduleFragment_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSubset: (string | null)[] | null;
  mode: string;
  runConfigYaml: string | null;
}

export interface OverviewScheduleFragment_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface OverviewScheduleFragment_runs_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface OverviewScheduleFragment_runs_stats_PythonError {
  __typename: "PythonError";
}

export interface OverviewScheduleFragment_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  endTime: number | null;
}

export type OverviewScheduleFragment_runs_stats = OverviewScheduleFragment_runs_stats_PythonError | OverviewScheduleFragment_runs_stats_PipelineRunStatsSnapshot;

export interface OverviewScheduleFragment_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: OverviewScheduleFragment_runs_pipeline;
  stats: OverviewScheduleFragment_runs_stats;
  status: PipelineRunStatus;
}

export interface OverviewScheduleFragment_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface OverviewScheduleFragment {
  __typename: "RunningSchedule";
  scheduleDefinition: OverviewScheduleFragment_scheduleDefinition;
  logsPath: string;
  ticks: OverviewScheduleFragment_ticks[];
  runsCount: number;
  runs: OverviewScheduleFragment_runs[];
  stats: OverviewScheduleFragment_stats;
  ticksCount: number;
  status: ScheduleStatus;
}
