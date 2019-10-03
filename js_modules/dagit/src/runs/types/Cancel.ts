// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: Cancel
// ====================================================

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  solids: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline_Pipeline_solids[];
}

export type Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline = Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline_UnknownPipeline | Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline_Pipeline;

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_stats {
  __typename: "PipelineRunStatsSnapshot";
  stepsSucceeded: number;
  stepsFailed: number;
  startTime: number | null;
  endTime: number | null;
  expectations: number;
  materializations: number;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_executionPlan {
  __typename: "ExecutionPlan";
  steps: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_executionPlan_steps[];
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canCancel: boolean;
  mode: string;
  environmentConfigYaml: string;
  pipeline: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_pipeline;
  stats: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_stats;
  tags: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_tags[];
  executionPlan: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run_executionPlan | null;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess {
  __typename: "CancelPipelineExecutionSuccess";
  run: Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess_run;
}

export interface Cancel_cancelPipelineExecution_CancelPipelineExecutionFailure {
  __typename: "CancelPipelineExecutionFailure";
  message: string;
}

export interface Cancel_cancelPipelineExecution_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
  message: string;
}

export type Cancel_cancelPipelineExecution = Cancel_cancelPipelineExecution_CancelPipelineExecutionSuccess | Cancel_cancelPipelineExecution_CancelPipelineExecutionFailure | Cancel_cancelPipelineExecution_PipelineRunNotFoundError;

export interface Cancel {
  cancelPipelineExecution: Cancel_cancelPipelineExecution;
}

export interface CancelVariables {
  runId: string;
}
