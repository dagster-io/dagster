

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarPipelineInfoFragment
// ====================================================

export interface SidebarPipelineInfoFragment_contexts_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: SidebarPipelineInfoFragment_contexts_config_type_RegularType_typeAttributes;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
  typeAttributes: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_RegularType_typeAttributes;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type_typeAttributes {
  isNamed: boolean;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
  typeAttributes: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type_typeAttributes;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  typeAttributes: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_typeAttributes;
  fields: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type = SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_RegularType | SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields_type;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarPipelineInfoFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_fields[];
  typeAttributes: SidebarPipelineInfoFragment_contexts_config_type_CompositeType_typeAttributes;
}

export type SidebarPipelineInfoFragment_contexts_config_type = SidebarPipelineInfoFragment_contexts_config_type_RegularType | SidebarPipelineInfoFragment_contexts_config_type_CompositeType;

export interface SidebarPipelineInfoFragment_contexts_config {
  type: SidebarPipelineInfoFragment_contexts_config_type;
}

export interface SidebarPipelineInfoFragment_contexts {
  name: string;
  description: string | null;
  config: SidebarPipelineInfoFragment_contexts_config | null;
}

export interface SidebarPipelineInfoFragment {
  name: string;
  description: string | null;
  contexts: SidebarPipelineInfoFragment_contexts[];
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