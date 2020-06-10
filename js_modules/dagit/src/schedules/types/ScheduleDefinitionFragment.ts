// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleDefinitionFragment
// ====================================================

export interface ScheduleDefinitionFragment_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface ScheduleDefinitionFragment_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
}

export interface ScheduleDefinitionFragment_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleDefinitionFragment_scheduleState_runs_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface ScheduleDefinitionFragment_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: ScheduleDefinitionFragment_scheduleState_runs_tags[];
  pipeline: ScheduleDefinitionFragment_scheduleState_runs_pipeline;
  status: PipelineRunStatus;
}

export interface ScheduleDefinitionFragment_scheduleState_stats {
  __typename: "ScheduleTickStatsSnapshot";
  ticksStarted: number;
  ticksSucceeded: number;
  ticksSkipped: number;
  ticksFailed: number;
}

export interface ScheduleDefinitionFragment_scheduleState {
  __typename: "ScheduleState";
  runningScheduleCount: number;
  ticks: ScheduleDefinitionFragment_scheduleState_ticks[];
  runsCount: number;
  runs: ScheduleDefinitionFragment_scheduleState_runs[];
  stats: ScheduleDefinitionFragment_scheduleState_stats;
  ticksCount: number;
  status: ScheduleStatus;
}

export interface ScheduleDefinitionFragment {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  runConfigYaml: string | null;
  partitionSet: ScheduleDefinitionFragment_partitionSet | null;
  scheduleState: ScheduleDefinitionFragment_scheduleState | null;
}
