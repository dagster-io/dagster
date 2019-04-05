/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunBarRunFragment
// ====================================================

export interface RunBarRunFragment_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface RunBarRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
}

export interface RunBarRunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunBarRunFragment_executionPlan_steps[];
}

export interface RunBarRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  config: string;
  pipeline: RunBarRunFragment_pipeline;
  executionPlan: RunBarRunFragment_executionPlan;
}
