

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerSolidFragment
// ====================================================

export interface PipelineExplorerSolidFragment_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes = PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType {
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes = PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  key: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType {
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_configType = PipelineExplorerSolidFragment_definition_configDefinition_configType_EnumConfigType | PipelineExplorerSolidFragment_definition_configDefinition_configType_CompositeConfigType;

export interface PipelineExplorerSolidFragment_definition_configDefinition {
  configType: PipelineExplorerSolidFragment_definition_configDefinition_configType;
}

export interface PipelineExplorerSolidFragment_definition {
  metadata: PipelineExplorerSolidFragment_definition_metadata[];
  configDefinition: PipelineExplorerSolidFragment_definition_configDefinition | null;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition_type {
  name: string | null;
  description: string | null;
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

export interface PipelineExplorerSolidFragment_outputs_definition_type {
  name: string | null;
  description: string | null;
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

export enum EvaluationErrorReason {
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
  RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH",
  SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR",
}

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
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================