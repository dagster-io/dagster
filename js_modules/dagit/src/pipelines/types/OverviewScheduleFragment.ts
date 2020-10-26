// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OverviewScheduleFragment
// ====================================================

export interface OverviewScheduleFragment_scheduleState_lastRuns_stats_PythonError {
  __typename: "PythonError";
}

export interface OverviewScheduleFragment_scheduleState_lastRuns_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  endTime: number | null;
}

export type OverviewScheduleFragment_scheduleState_lastRuns_stats = OverviewScheduleFragment_scheduleState_lastRuns_stats_PythonError | OverviewScheduleFragment_scheduleState_lastRuns_stats_PipelineRunStatsSnapshot;

export interface OverviewScheduleFragment_scheduleState_lastRuns {
  __typename: "PipelineRun";
  stats: OverviewScheduleFragment_scheduleState_lastRuns_stats;
}

export interface OverviewScheduleFragment_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface OverviewScheduleFragment_scheduleState {
  __typename: "ScheduleState";
  runsCount: number;
  lastRuns: OverviewScheduleFragment_scheduleState_lastRuns[];
  runs: OverviewScheduleFragment_scheduleState_runs[];
  status: ScheduleStatus;
}

export interface OverviewScheduleFragment {
  __typename: "ScheduleDefinition";
  name: string;
  scheduleState: OverviewScheduleFragment_scheduleState | null;
}
