// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewScheduleFragment
// ====================================================

export interface OverviewScheduleFragment_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface OverviewScheduleFragment_scheduleState_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface OverviewScheduleFragment_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface OverviewScheduleFragment_scheduleState_runs_stats_PythonError {
  __typename: "PythonError";
}

export interface OverviewScheduleFragment_scheduleState_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  endTime: number | null;
}

export type OverviewScheduleFragment_scheduleState_runs_stats = OverviewScheduleFragment_scheduleState_runs_stats_PythonError | OverviewScheduleFragment_scheduleState_runs_stats_PipelineRunStatsSnapshot;

export interface OverviewScheduleFragment_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  pipeline: OverviewScheduleFragment_scheduleState_runs_pipeline;
  tags: OverviewScheduleFragment_scheduleState_runs_tags[];
  stats: OverviewScheduleFragment_scheduleState_runs_stats;
  status: PipelineRunStatus;
}

export interface OverviewScheduleFragment_scheduleState_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface OverviewScheduleFragment_scheduleState {
  __typename: "ScheduleState";
  ticks: OverviewScheduleFragment_scheduleState_ticks[];
  runsCount: number;
  runs: OverviewScheduleFragment_scheduleState_runs[];
  stats: OverviewScheduleFragment_scheduleState_stats;
  ticksCount: number;
  status: ScheduleStatus;
}

export interface OverviewScheduleFragment {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  runConfigYaml: string | null;
  scheduleState: OverviewScheduleFragment_scheduleState | null;
}
