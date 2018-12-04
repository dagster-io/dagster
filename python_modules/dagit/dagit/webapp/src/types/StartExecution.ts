

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StartExecution
// ====================================================

export interface StartExecution_startPipelineExecution_StartPipelineExecutionSuccess_run {
  runId: string;
}

export interface StartExecution_startPipelineExecution_StartPipelineExecutionSuccess {
  __typename: "StartPipelineExecutionSuccess";
  run: StartExecution_startPipelineExecution_StartPipelineExecutionSuccess_run;
}

export interface StartExecution_startPipelineExecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface StartExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors {
  message: string;
}

export interface StartExecution_startPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: StartExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export type StartExecution_startPipelineExecution = StartExecution_startPipelineExecution_StartPipelineExecutionSuccess | StartExecution_startPipelineExecution_PipelineNotFoundError | StartExecution_startPipelineExecution_PipelineConfigValidationInvalid;

export interface StartExecution {
  startPipelineExecution: StartExecution_startPipelineExecution;
}

export interface StartExecutionVariables {
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