

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigExplorerFragment
// ====================================================

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType_fields[];
}

export type ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes = ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_RegularType | ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes_CompositeType;

export interface ConfigExplorerFragment_contexts_config_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_type_RegularType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_contexts_config_type_RegularType_typeAttributes;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes = ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_RegularType | ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes_CompositeType;

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type {
  name: string;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigExplorerFragment_contexts_config_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigExplorerFragment_contexts_config_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_contexts_config_type_CompositeType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_contexts_config_type_CompositeType_typeAttributes;
  fields: ConfigExplorerFragment_contexts_config_type_CompositeType_fields[];
}

export type ConfigExplorerFragment_contexts_config_type = ConfigExplorerFragment_contexts_config_type_RegularType | ConfigExplorerFragment_contexts_config_type_CompositeType;

export interface ConfigExplorerFragment_contexts_config {
  type: ConfigExplorerFragment_contexts_config_type;
}

export interface ConfigExplorerFragment_contexts {
  name: string;
  description: string | null;
  config: ConfigExplorerFragment_contexts_config | null;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes = ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_RegularType | ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes_CompositeType;

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType_typeAttributes;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes = ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_RegularType | ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes_CompositeType;

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_innerTypes[];
  typeAttributes: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_typeAttributes;
  fields: ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType_fields[];
}

export type ConfigExplorerFragment_solids_definition_configDefinition_type = ConfigExplorerFragment_solids_definition_configDefinition_type_RegularType | ConfigExplorerFragment_solids_definition_configDefinition_type_CompositeType;

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
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
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