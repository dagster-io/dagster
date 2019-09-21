// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunHistoryRunFragment
// ====================================================

export interface RunHistoryRunFragment_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
}

export interface RunHistoryRunFragment_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunHistoryRunFragment_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunHistoryRunFragment_pipeline_Pipeline_solids[];
}

export type RunHistoryRunFragment_pipeline = RunHistoryRunFragment_pipeline_UnknownPipeline | RunHistoryRunFragment_pipeline_Pipeline;

export interface RunHistoryRunFragment_stats {
  __typename: "PipelineRunStatsSnapshot";
  stepsSucceeded: number;
  stepsFailed: number;
  startTime: number | null;
  endTime: number | null;
  expectations: number;
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
  stepKeysToExecute: string[] | null;
  mode: string;
  environmentConfigYaml: string;
  pipeline: RunHistoryRunFragment_pipeline;
  stats: RunHistoryRunFragment_stats;
  executionPlan: RunHistoryRunFragment_executionPlan | null;
}
