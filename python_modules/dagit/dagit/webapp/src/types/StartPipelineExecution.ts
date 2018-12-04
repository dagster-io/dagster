

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StartPipelineExecution
// ====================================================

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run {
  runId: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess {
  __typename: "StartPipelineExecutionSuccess";
  run: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors {
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export type StartPipelineExecution_startPipelineExecution = StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess | StartPipelineExecution_startPipelineExecution_PipelineNotFoundError | StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid;

export interface StartPipelineExecution {
  startPipelineExecution: StartPipelineExecution_startPipelineExecution;
}

export interface StartPipelineExecutionVariables {
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