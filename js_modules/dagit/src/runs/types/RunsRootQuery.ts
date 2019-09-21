// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunsRootQuery
// ====================================================

export interface RunsRootQuery_pipelineRuns_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
}

export interface RunsRootQuery_pipelineRuns_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunsRootQuery_pipelineRuns_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunsRootQuery_pipelineRuns_pipeline_Pipeline_solids[];
}

export type RunsRootQuery_pipelineRuns_pipeline = RunsRootQuery_pipelineRuns_pipeline_UnknownPipeline | RunsRootQuery_pipelineRuns_pipeline_Pipeline;

export interface RunsRootQuery_pipelineRuns_stats {
  __typename: "PipelineRunStatsSnapshot";
  stepsSucceeded: number;
  stepsFailed: number;
  startTime: number | null;
  endTime: number | null;
  expectations: number;
  materializations: number;
}

export interface RunsRootQuery_pipelineRuns_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
}

export interface RunsRootQuery_pipelineRuns_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunsRootQuery_pipelineRuns_executionPlan_steps[];
}

export interface RunsRootQuery_pipelineRuns {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  mode: string;
  environmentConfigYaml: string;
  pipeline: RunsRootQuery_pipelineRuns_pipeline;
  stats: RunsRootQuery_pipelineRuns_stats;
  executionPlan: RunsRootQuery_pipelineRuns_executionPlan | null;
}

export interface RunsRootQuery {
  pipelineRuns: RunsRootQuery_pipelineRuns[];
}
