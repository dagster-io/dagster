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

export interface RunHistoryRunFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "PipelineProcessExitedEvent" | "PipelineProcessStartedEvent" | "PipelineProcessStartEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "ObjectStoreOperationEvent" | "StepMaterializationEvent" | "EngineEvent";
  timestamp: string;
}

export interface RunHistoryRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface RunHistoryRunFragment_logs_nodes_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  timestamp: string;
  expectationResult: RunHistoryRunFragment_logs_nodes_StepExpectationResultEvent_expectationResult;
}

export type RunHistoryRunFragment_logs_nodes = RunHistoryRunFragment_logs_nodes_ExecutionStepFailureEvent | RunHistoryRunFragment_logs_nodes_StepExpectationResultEvent;

export interface RunHistoryRunFragment_logs {
  __typename: "LogMessageConnection";
  nodes: RunHistoryRunFragment_logs_nodes[];
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
  logs: RunHistoryRunFragment_logs;
  executionPlan: RunHistoryRunFragment_executionPlan;
}
