

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionFragment
// ====================================================

export interface PipelineExecutionFragment_environmentType {
  name: string;
}

export interface PipelineExecutionFragment_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelineExecutionFragment_runs_logs_nodes {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
}

export interface PipelineExecutionFragment_runs_logs {
  pageInfo: PipelineExecutionFragment_runs_logs_pageInfo;
  nodes: PipelineExecutionFragment_runs_logs_nodes[];
}

export interface PipelineExecutionFragment_runs_executionPlan_steps_solid {
  name: string;
}

export interface PipelineExecutionFragment_runs_executionPlan_steps {
  name: string;
  solid: PipelineExecutionFragment_runs_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineExecutionFragment_runs_executionPlan {
  steps: PipelineExecutionFragment_runs_executionPlan_steps[];
}

export interface PipelineExecutionFragment_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionFragment_runs_logs;
  executionPlan: PipelineExecutionFragment_runs_executionPlan;
}

export interface PipelineExecutionFragment {
  name: string;
  environmentType: PipelineExecutionFragment_environmentType;
  runs: PipelineExecutionFragment_runs[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  JOIN = "JOIN",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================