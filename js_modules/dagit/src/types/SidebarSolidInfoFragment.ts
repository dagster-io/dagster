

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidInfoFragment
// ====================================================

export interface SidebarSolidInfoFragment_outputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_outputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: SidebarSolidInfoFragment_outputs_definition_type_typeAttributes;
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

export interface SidebarSolidInfoFragment_inputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_inputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: SidebarSolidInfoFragment_inputs_definition_type_typeAttributes;
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

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes = SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_RegularType | SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes_CompositeType;

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_innerTypes[];
  typeAttributes: SidebarSolidInfoFragment_definition_configDefinition_type_RegularType_typeAttributes;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes = SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_RegularType | SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes_CompositeType;

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type {
  name: string;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_innerTypes[];
  typeAttributes: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_typeAttributes;
  fields: SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType_fields[];
}

export type SidebarSolidInfoFragment_definition_configDefinition_type = SidebarSolidInfoFragment_definition_configDefinition_type_RegularType | SidebarSolidInfoFragment_definition_configDefinition_type_CompositeType;

export interface SidebarSolidInfoFragment_definition_configDefinition {
  type: SidebarSolidInfoFragment_definition_configDefinition_type;
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