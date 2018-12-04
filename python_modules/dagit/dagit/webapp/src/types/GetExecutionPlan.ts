

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: GetExecutionPlan
// ====================================================

export interface GetExecutionPlan_executionPlan_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid" | "PipelineNotFoundError";
}

export interface GetExecutionPlan_executionPlan_ExecutionPlan_steps_solid {
  name: string;
}

export interface GetExecutionPlan_executionPlan_ExecutionPlan_steps {
  name: string;
  solid: GetExecutionPlan_executionPlan_ExecutionPlan_steps_solid;
  tag: StepTag;
}

export interface GetExecutionPlan_executionPlan_ExecutionPlan {
  __typename: "ExecutionPlan";
  steps: GetExecutionPlan_executionPlan_ExecutionPlan_steps[];
}

export type GetExecutionPlan_executionPlan = GetExecutionPlan_executionPlan_PipelineConfigValidationInvalid | GetExecutionPlan_executionPlan_ExecutionPlan;

export interface GetExecutionPlan {
  executionPlan: GetExecutionPlan_executionPlan;
}

export interface GetExecutionPlanVariables {
  executionParams: PipelineExecutionParams;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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