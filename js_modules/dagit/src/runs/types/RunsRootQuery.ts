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

export interface RunsRootQuery_pipelineRuns_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "PipelineProcessExitedEvent" | "PipelineProcessStartedEvent" | "PipelineProcessStartEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "ObjectStoreOperationEvent" | "StepMaterializationEvent" | "EngineEvent";
  timestamp: string;
}

export interface RunsRootQuery_pipelineRuns_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface RunsRootQuery_pipelineRuns_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  timestamp: string;
  expectationResult: RunsRootQuery_pipelineRuns_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export type RunsRootQuery_pipelineRuns_logs_nodes = RunsRootQuery_pipelineRuns_logs_nodes_ExecutionStepFailureEvent | RunsRootQuery_pipelineRuns_logs_nodes_StepExpectationResultEvent;

export interface RunsRootQuery_pipelineRuns_logs {
  __typename: "LogMessageConnection";
  nodes: RunsRootQuery_pipelineRuns_logs_nodes[];
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
  logs: RunsRootQuery_pipelineRuns_logs;
  executionPlan: RunsRootQuery_pipelineRuns_executionPlan | null;
}

export interface RunsRootQuery {
  pipelineRuns: RunsRootQuery_pipelineRuns[];
}
