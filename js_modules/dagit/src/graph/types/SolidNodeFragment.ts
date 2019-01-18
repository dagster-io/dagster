

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidNodeFragment
// ====================================================

export interface SolidNodeFragment_definition_metadata {
  key: string;
  value: string;
}

export interface SolidNodeFragment_definition_configDefinition_type {
  name: string;
  description: string | null;
}

export interface SolidNodeFragment_definition_configDefinition {
  type: SolidNodeFragment_definition_configDefinition_type;
}

export interface SolidNodeFragment_definition {
  metadata: SolidNodeFragment_definition_metadata[];
  configDefinition: SolidNodeFragment_definition_configDefinition | null;
}

export interface SolidNodeFragment_inputs_definition_type {
  name: string;
}

export interface SolidNodeFragment_inputs_definition {
  name: string;
  type: SolidNodeFragment_inputs_definition_type;
}

export interface SolidNodeFragment_inputs_dependsOn_definition {
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SolidNodeFragment_inputs_dependsOn {
  definition: SolidNodeFragment_inputs_dependsOn_definition;
  solid: SolidNodeFragment_inputs_dependsOn_solid;
}

export interface SolidNodeFragment_inputs {
  definition: SolidNodeFragment_inputs_definition;
  dependsOn: SolidNodeFragment_inputs_dependsOn | null;
}

export interface SolidNodeFragment_outputs_definition_type {
  name: string;
}

export interface SolidNodeFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SolidNodeFragment_outputs_definition {
  name: string;
  type: SolidNodeFragment_outputs_definition_type;
  expectations: SolidNodeFragment_outputs_definition_expectations[];
}

export interface SolidNodeFragment_outputs_dependedBy_solid {
  name: string;
}

export interface SolidNodeFragment_outputs_dependedBy {
  solid: SolidNodeFragment_outputs_dependedBy_solid;
}

export interface SolidNodeFragment_outputs {
  definition: SolidNodeFragment_outputs_definition;
  dependedBy: SolidNodeFragment_outputs_dependedBy[];
}

export interface SolidNodeFragment {
  name: string;
  definition: SolidNodeFragment_definition;
  inputs: SolidNodeFragment_inputs[];
  outputs: SolidNodeFragment_outputs[];
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