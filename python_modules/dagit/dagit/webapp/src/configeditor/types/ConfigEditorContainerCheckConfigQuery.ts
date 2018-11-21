

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigEditorContainerCheckConfigQuery
// ====================================================

export interface ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid";
}

export interface ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors {
  message: string;
  path: string[];
}

export interface ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors[];
}

export type ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid = ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid | ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid;

export interface ConfigEditorContainerCheckConfigQuery {
  isPipelineConfigValid: ConfigEditorContainerCheckConfigQuery_isPipelineConfigValid;
}

export interface ConfigEditorContainerCheckConfigQueryVariables {
  pipelineName: string;
  config: any;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================