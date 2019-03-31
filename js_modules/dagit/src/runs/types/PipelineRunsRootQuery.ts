/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunsRootQuery
// ====================================================

export interface PipelineRunsRootQuery_pipeline_runs_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface PipelineRunsRootQuery_pipeline_runs_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunsRootQuery_pipeline_runs_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunsRootQuery_pipeline_runs_executionPlan_steps[];
}

export interface PipelineRunsRootQuery_pipeline_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  config: string;
  pipeline: PipelineRunsRootQuery_pipeline_runs_pipeline;
  executionPlan: PipelineRunsRootQuery_pipeline_runs_executionPlan;
}

export interface PipelineRunsRootQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  runs: PipelineRunsRootQuery_pipeline_runs[];
}

export interface PipelineRunsRootQuery {
  pipeline: PipelineRunsRootQuery_pipeline;
}

export interface PipelineRunsRootQueryVariables {
  name: string;
}
