/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunHistoryRunFragment
// ====================================================

export interface RunHistoryRunFragment_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface RunHistoryRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunHistoryRunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunHistoryRunFragment_executionPlan_steps[];
}

export interface RunHistoryRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  config: string;
  pipeline: RunHistoryRunFragment_pipeline;
  executionPlan: RunHistoryRunFragment_executionPlan;
}
