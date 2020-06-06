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
  solidSelection: (string | null)[] | null;
  mode: string;
  runConfigYaml: string | null;
}

export interface ScheduleFragment_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface ScheduleFragment_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleFragment_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface ScheduleFragment_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: ScheduleFragment_runs_tags[];
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
  runningScheduleCount: number;
  scheduleDefinition: ScheduleFragment_scheduleDefinition;
  ticks: ScheduleFragment_ticks[];
  runsCount: number;
  runs: ScheduleFragment_runs[];
  stats: ScheduleFragment_stats;
  ticksCount: number;
  status: ScheduleStatus;
}
