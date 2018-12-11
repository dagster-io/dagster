

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigExplorerFragment
// ====================================================

export interface ConfigExplorerFragment_types_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_types_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: ConfigExplorerFragment_types_RegularType_typeAttributes;
}

export interface ConfigExplorerFragment_types_CompositeType_fields_type {
  __typename: "RegularType" | "CompositeType";
  name: string;
}

export interface ConfigExplorerFragment_types_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigExplorerFragment_types_CompositeType_fields_type;
}

export interface ConfigExplorerFragment_types_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_types_CompositeType {
  __typename: "CompositeType";
  fields: ConfigExplorerFragment_types_CompositeType_fields[];
  name: string;
  description: string | null;
  typeAttributes: ConfigExplorerFragment_types_CompositeType_typeAttributes;
}

export type ConfigExplorerFragment_types = ConfigExplorerFragment_types_RegularType | ConfigExplorerFragment_types_CompositeType;

export interface ConfigExplorerFragment_contexts_config_type_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type {
  name: string;
  description: string | null;
  typeAttributes: ConfigExplorerFragment_contexts_config_type_typeAttributes;
  __typename: "RegularType" | "CompositeType";
}

export interface ConfigExplorerFragment_contexts_config {
  type: ConfigExplorerFragment_contexts_config_type;
}

export interface ConfigExplorerFragment_contexts {
  name: string;
  description: string | null;
  config: ConfigExplorerFragment_contexts_config | null;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type {
  name: string;
  description: string | null;
  typeAttributes: ConfigExplorerFragment_solids_definition_configDefinition_type_typeAttributes;
  __typename: "RegularType" | "CompositeType";
}

export interface ConfigExplorerFragment_solids_definition_configDefinition {
  type: ConfigExplorerFragment_solids_definition_configDefinition_type;
}

export interface ConfigExplorerFragment_solids_definition {
  name: string;
  description: string | null;
  configDefinition: ConfigExplorerFragment_solids_definition_configDefinition | null;
}

export interface ConfigExplorerFragment_solids {
  definition: ConfigExplorerFragment_solids_definition;
}

export interface ConfigExplorerFragment {
  types: ConfigExplorerFragment_types[];
  contexts: ConfigExplorerFragment_contexts[];
  solids: ConfigExplorerFragment_solids[];
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