

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidInfoFragment
// ====================================================

export interface SidebarSolidInfoFragment_outputs_definition_type {
  name: string | null;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_outputs_definition {
  name: string;
  type: SidebarSolidInfoFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_outputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_outputs {
  definition: SidebarSolidInfoFragment_outputs_definition;
}

export interface SidebarSolidInfoFragment_inputs_definition_type {
  name: string | null;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarSolidInfoFragment_inputs_definition {
  name: string;
  type: SidebarSolidInfoFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarSolidInfoFragment_inputs_definition_expectations[];
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_definition {
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SidebarSolidInfoFragment_inputs_dependsOn {
  definition: SidebarSolidInfoFragment_inputs_dependsOn_definition;
  solid: SidebarSolidInfoFragment_inputs_dependsOn_solid;
}

export interface SidebarSolidInfoFragment_inputs {
  definition: SidebarSolidInfoFragment_inputs_definition;
  dependsOn: SidebarSolidInfoFragment_inputs_dependsOn | null;
}

export interface SidebarSolidInfoFragment_definition_metadata {
  key: string;
  value: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes = SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes = SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  key: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_configType = SidebarSolidInfoFragment_definition_configDefinition_configType_EnumConfigType | SidebarSolidInfoFragment_definition_configDefinition_configType_CompositeConfigType;

export interface SidebarSolidInfoFragment_definition_configDefinition {
  configType: SidebarSolidInfoFragment_definition_configDefinition_configType;
}

export interface SidebarSolidInfoFragment_definition {
  description: string | null;
  metadata: SidebarSolidInfoFragment_definition_metadata[];
  configDefinition: SidebarSolidInfoFragment_definition_configDefinition | null;
}

export interface SidebarSolidInfoFragment {
  outputs: SidebarSolidInfoFragment_outputs[];
  inputs: SidebarSolidInfoFragment_inputs[];
  name: string;
  definition: SidebarSolidInfoFragment_definition;
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