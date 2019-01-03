

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerSolidFragment
// ====================================================

export interface PipelineExplorerSolidFragment_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes = PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType | PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType;

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType {
  description: string | null;
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_innerTypes[];
  typeAttributes: PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType_typeAttributes;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes = PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType | PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType;

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType {
  description: string | null;
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_innerTypes[];
  typeAttributes: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_typeAttributes;
  fields: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_type = PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType | PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType;

export interface PipelineExplorerSolidFragment_definition_configDefinition {
  type: PipelineExplorerSolidFragment_definition_configDefinition_type;
}

export interface PipelineExplorerSolidFragment_definition {
  metadata: PipelineExplorerSolidFragment_definition_metadata[];
  configDefinition: PipelineExplorerSolidFragment_definition_configDefinition | null;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_inputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: PipelineExplorerSolidFragment_inputs_definition_type_typeAttributes;
}

export interface PipelineExplorerSolidFragment_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition {
  name: string;
  type: PipelineExplorerSolidFragment_inputs_definition_type;
  description: string | null;
  expectations: PipelineExplorerSolidFragment_inputs_definition_expectations[];
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn {
  definition: PipelineExplorerSolidFragment_inputs_dependsOn_definition;
  solid: PipelineExplorerSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineExplorerSolidFragment_inputs {
  definition: PipelineExplorerSolidFragment_inputs_definition;
  dependsOn: PipelineExplorerSolidFragment_inputs_dependsOn | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface PipelineExplorerSolidFragment_outputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: PipelineExplorerSolidFragment_outputs_definition_type_typeAttributes;
}

export interface PipelineExplorerSolidFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition {
  name: string;
  type: PipelineExplorerSolidFragment_outputs_definition_type;
  expectations: PipelineExplorerSolidFragment_outputs_definition_expectations[];
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy_solid {
  name: string;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy {
  solid: PipelineExplorerSolidFragment_outputs_dependedBy_solid;
}

export interface PipelineExplorerSolidFragment_outputs {
  definition: PipelineExplorerSolidFragment_outputs_definition;
  dependedBy: PipelineExplorerSolidFragment_outputs_dependedBy[];
}

export interface PipelineExplorerSolidFragment {
  name: string;
  definition: PipelineExplorerSolidFragment_definition;
  inputs: PipelineExplorerSolidFragment_inputs[];
  outputs: PipelineExplorerSolidFragment_outputs[];
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