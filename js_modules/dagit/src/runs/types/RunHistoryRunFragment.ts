// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunHistoryRunFragment
// ====================================================

export interface RunHistoryRunFragment_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface RunHistoryRunFragment_stats {
  __typename: "PipelineRunStats";
  stepsSucceeded: number;
  stepsFailed: number;
  startTime: number | null;
  endTime: number | null;
  expectationsFailed: number;
  expectationsSucceeded: number;
  materializations: number;
}

export interface RunHistoryRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunHistoryRunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunHistoryRunFragment_executionPlan_steps[];
}

export interface RunHistoryRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: (string | null)[] | null;
  mode: string;
  environmentConfigYaml: string;
  pipeline: RunHistoryRunFragment_pipeline;
  stats: RunHistoryRunFragment_stats;
  executionPlan: RunHistoryRunFragment_executionPlan;
}
