// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunsRootQuery
// ====================================================

export interface PipelineRunsRootQuery_pipelineOrError_PythonError {
  __typename: "PythonError" | "SolidNotFoundError";
}

export interface PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_logs_nodes {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "PipelineProcessStartedEvent" | "PipelineProcessStartEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "ObjectStoreOperationEvent" | "StepExpectationResultEvent" | "StepMaterializationEvent";
  timestamp: string;
}

export interface PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_logs {
  __typename: "LogMessageConnection";
  nodes: PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_logs_nodes[];
}

export interface PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_executionPlan_steps[];
}

export interface PipelineRunsRootQuery_pipelineOrError_Pipeline_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_pipeline;
  logs: PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_logs;
  executionPlan: PipelineRunsRootQuery_pipelineOrError_Pipeline_runs_executionPlan;
}

export interface PipelineRunsRootQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  name: string;
  runs: PipelineRunsRootQuery_pipelineOrError_Pipeline_runs[];
}

export interface PipelineRunsRootQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export type PipelineRunsRootQuery_pipelineOrError = PipelineRunsRootQuery_pipelineOrError_PythonError | PipelineRunsRootQuery_pipelineOrError_Pipeline | PipelineRunsRootQuery_pipelineOrError_PipelineNotFoundError;

export interface PipelineRunsRootQuery {
  pipelineOrError: PipelineRunsRootQuery_pipelineOrError;
}

export interface PipelineRunsRootQueryVariables {
  name: string;
}
