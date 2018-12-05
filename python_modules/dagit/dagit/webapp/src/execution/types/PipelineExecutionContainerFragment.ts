

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionContainerFragment
// ====================================================

export interface PipelineExecutionContainerFragment_runs_logs_pageInfo {
  lastCursor: any | null;
}

export interface PipelineExecutionContainerFragment_runs_logs_nodes {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
}

export interface PipelineExecutionContainerFragment_runs_logs {
  pageInfo: PipelineExecutionContainerFragment_runs_logs_pageInfo;
  nodes: PipelineExecutionContainerFragment_runs_logs_nodes[];
}

export interface PipelineExecutionContainerFragment_runs_executionPlan_steps_solid {
  name: string;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan_steps {
  name: string;
  solid: PipelineExecutionContainerFragment_runs_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineExecutionContainerFragment_runs_executionPlan {
  steps: PipelineExecutionContainerFragment_runs_executionPlan_steps[];
}

export interface PipelineExecutionContainerFragment_runs {
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionContainerFragment_runs_logs;
  executionPlan: PipelineExecutionContainerFragment_runs_executionPlan;
}

export interface PipelineExecutionContainerFragment_environmentType {
  name: string;
}

export interface PipelineExecutionContainerFragment {
  name: string;
  runs: PipelineExecutionContainerFragment_runs[];
  environmentType: PipelineExecutionContainerFragment_environmentType;
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