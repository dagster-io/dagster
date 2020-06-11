// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleStateFragment
// ====================================================

export interface ScheduleStateFragment_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface ScheduleStateFragment_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleStateFragment_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface ScheduleStateFragment_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: ScheduleStateFragment_runs_tags[];
  pipeline: ScheduleStateFragment_runs_pipeline;
  status: PipelineRunStatus;
}

export interface ScheduleStateFragment_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface ScheduleStateFragment {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: ScheduleStateFragment_ticks[];
  runsCount: number;
  runs: ScheduleStateFragment_runs[];
  stats: ScheduleStateFragment_stats;
  ticksCount: number;
  status: ScheduleStatus;
}
