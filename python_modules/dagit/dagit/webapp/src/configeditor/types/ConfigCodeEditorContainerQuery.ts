

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigCodeEditorContainerQuery
// ====================================================

export interface ConfigCodeEditorContainerQuery_types_RegularType {
  __typename: "RegularType";
  name: string;
}

export interface ConfigCodeEditorContainerQuery_types_CompositeType_fields_type {
  name: string;
}

export interface ConfigCodeEditorContainerQuery_types_CompositeType_fields {
  name: string;
  type: ConfigCodeEditorContainerQuery_types_CompositeType_fields_type;
}

export interface ConfigCodeEditorContainerQuery_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  fields: ConfigCodeEditorContainerQuery_types_CompositeType_fields[];
}

export type ConfigCodeEditorContainerQuery_types = ConfigCodeEditorContainerQuery_types_RegularType | ConfigCodeEditorContainerQuery_types_CompositeType;

export interface ConfigCodeEditorContainerQuery {
  types: ConfigCodeEditorContainerQuery_types[];
}

export interface ConfigCodeEditorContainerQueryVariables {
  pipelineName: string;
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