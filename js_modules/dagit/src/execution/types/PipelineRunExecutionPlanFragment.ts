

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineRunExecutionPlanFragment
// ====================================================

export interface PipelineRunExecutionPlanFragment_executionPlan_steps_solid {
  name: string;
}

export interface PipelineRunExecutionPlanFragment_executionPlan_steps {
  name: string;
  solid: PipelineRunExecutionPlanFragment_executionPlan_steps_solid;
  tag: StepTag;
}

export interface PipelineRunExecutionPlanFragment_executionPlan {
  steps: PipelineRunExecutionPlanFragment_executionPlan_steps[];
}

export interface PipelineRunExecutionPlanFragment {
  executionPlan: PipelineRunExecutionPlanFragment_executionPlan;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

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