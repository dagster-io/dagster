/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunHistoryQuery
// ====================================================

export interface RunHistoryQuery_pipelineRuns_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface RunHistoryQuery_pipelineRuns_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunHistoryQuery_pipelineRuns_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunHistoryQuery_pipelineRuns_executionPlan_steps[];
}

export interface RunHistoryQuery_pipelineRuns {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  config: string;
  pipeline: RunHistoryQuery_pipelineRuns_pipeline;
  executionPlan: RunHistoryQuery_pipelineRuns_executionPlan;
}

export interface RunHistoryQuery {
  pipelineRuns: RunHistoryQuery_pipelineRuns[];
}
