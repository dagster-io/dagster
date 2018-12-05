

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineRunFragment
// ====================================================

export interface PipelineRunFragment_logs_nodes {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent";
  message: string;
}

export interface PipelineRunFragment_logs {
  nodes: PipelineRunFragment_logs_nodes[];
}

export interface PipelineRunFragment_executionPlan_steps_solid {
  name: string;
}

export interface PipelineRunFragment_executionPlan_steps {
  name: string;
  solid: PipelineRunFragment_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineRunFragment_executionPlan {
  steps: PipelineRunFragment_executionPlan_steps[];
}

export interface PipelineRunFragment {
  logs: PipelineRunFragment_logs;
  executionPlan: PipelineRunFragment_executionPlan;
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