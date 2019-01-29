

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarTabbedContainerSolidFragment
// ====================================================

export interface SidebarTabbedContainerSolidFragment_outputs_definition_type {
  name: string | null;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition {
  name: string;
  type: SidebarTabbedContainerSolidFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_outputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_outputs {
  definition: SidebarTabbedContainerSolidFragment_outputs_definition;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_type {
  name: string | null;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition {
  name: string;
  type: SidebarTabbedContainerSolidFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_inputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition {
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn {
  definition: SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition;
  solid: SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid;
}

export interface SidebarTabbedContainerSolidFragment_inputs {
  definition: SidebarTabbedContainerSolidFragment_inputs_definition;
  dependsOn: SidebarTabbedContainerSolidFragment_inputs_dependsOn | null;
}

export interface SidebarTabbedContainerSolidFragment_definition_metadata {
  key: string;
  value: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes = SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes = SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType {
  key: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType_fields[];
}

export type SidebarTabbedContainerSolidFragment_definition_configDefinition_configType = SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_EnumConfigType | SidebarTabbedContainerSolidFragment_definition_configDefinition_configType_CompositeConfigType;

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition {
  configType: SidebarTabbedContainerSolidFragment_definition_configDefinition_configType;
}

export interface SidebarTabbedContainerSolidFragment_definition {
  description: string | null;
  metadata: SidebarTabbedContainerSolidFragment_definition_metadata[];
  configDefinition: SidebarTabbedContainerSolidFragment_definition_configDefinition | null;
}

export interface SidebarTabbedContainerSolidFragment {
  outputs: SidebarTabbedContainerSolidFragment_outputs[];
  inputs: SidebarTabbedContainerSolidFragment_inputs[];
  name: string;
  definition: SidebarTabbedContainerSolidFragment_definition;
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

export enum StepKind {
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