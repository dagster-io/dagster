

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionFragment
// ====================================================

export interface PipelineExecutionFragment_environmentType {
  name: string;
}

export interface PipelineExecutionFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type = PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_RegularType | PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface PipelineExecutionFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExecutionFragment_contexts_config_type_CompositeType_fields_type;
}

export interface PipelineExecutionFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: PipelineExecutionFragment_contexts_config_type_CompositeType_fields[];
}

export type PipelineExecutionFragment_contexts_config_type = PipelineExecutionFragment_contexts_config_type_RegularType | PipelineExecutionFragment_contexts_config_type_CompositeType;

export interface PipelineExecutionFragment_contexts_config {
  type: PipelineExecutionFragment_contexts_config_type;
}

export interface PipelineExecutionFragment_contexts {
  config: PipelineExecutionFragment_contexts_config | null;
}

export interface PipelineExecutionFragment {
  name: string;
  environmentType: PipelineExecutionFragment_environmentType;
  contexts: PipelineExecutionFragment_contexts[];
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