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

export interface RunHistoryRunFragment_logs_nodes {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "StepExpectationResultEvent" | "StepMaterializationEvent";
  timestamp: string;
}

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
  pipeline: RunHistoryRunFragment_pipeline;
  logs: RunHistoryRunFragment_logs;
  executionPlan: RunHistoryRunFragment_executionPlan;
}
