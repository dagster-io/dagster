

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigCodeEditorContainerCheckConfigQuery
// ====================================================

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid";
}

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors {
  message: string;
  path: string[];
}

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors[];
}

export type ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid = ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid | ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid;

export interface ConfigCodeEditorContainerCheckConfigQuery {
  isPipelineConfigValid: ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid;
}

export interface ConfigCodeEditorContainerCheckConfigQueryVariables {
  executionParams: PipelineExecutionParams;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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