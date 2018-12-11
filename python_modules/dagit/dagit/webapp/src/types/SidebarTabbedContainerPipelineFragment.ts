

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarTabbedContainerPipelineFragment
// ====================================================

export interface SidebarTabbedContainerPipelineFragment_environmentType {
  name: string;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: SidebarTabbedContainerPipelineFragment_contexts_config_type_RegularType_typeAttributes;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
  typeAttributes: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_RegularType_typeAttributes;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
  typeAttributes: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type_typeAttributes;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  typeAttributes: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_typeAttributes;
  fields: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType_fields[];
}

export type SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type = SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_RegularType | SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type_CompositeType;

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields_type;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_fields[];
  typeAttributes: SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType_typeAttributes;
}

export type SidebarTabbedContainerPipelineFragment_contexts_config_type = SidebarTabbedContainerPipelineFragment_contexts_config_type_RegularType | SidebarTabbedContainerPipelineFragment_contexts_config_type_CompositeType;

export interface SidebarTabbedContainerPipelineFragment_contexts_config {
  type: SidebarTabbedContainerPipelineFragment_contexts_config_type;
}

export interface SidebarTabbedContainerPipelineFragment_contexts {
  name: string;
  description: string | null;
  config: SidebarTabbedContainerPipelineFragment_contexts_config | null;
}

export interface SidebarTabbedContainerPipelineFragment {
  name: string;
  environmentType: SidebarTabbedContainerPipelineFragment_environmentType;
  description: string | null;
  contexts: SidebarTabbedContainerPipelineFragment_contexts[];
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