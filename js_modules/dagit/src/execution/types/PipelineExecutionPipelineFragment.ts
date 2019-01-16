

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineFragment
// ====================================================

export interface PipelineExecutionPipelineFragment_environmentType {
  name: string;
}

export interface PipelineExecutionPipelineFragment_types_RegularType {
  __typename: "RegularType";
  name: string;
  isSelector: boolean;
}

export interface PipelineExecutionPipelineFragment_types_CompositeType_fields_type {
  name: string;
}

export interface PipelineExecutionPipelineFragment_types_CompositeType_fields {
  name: string;
  isOptional: boolean;
  type: PipelineExecutionPipelineFragment_types_CompositeType_fields_type;
}

export interface PipelineExecutionPipelineFragment_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  isSelector: boolean;
  fields: PipelineExecutionPipelineFragment_types_CompositeType_fields[];
}

export type PipelineExecutionPipelineFragment_types = PipelineExecutionPipelineFragment_types_RegularType | PipelineExecutionPipelineFragment_types_CompositeType;

export interface PipelineExecutionPipelineFragment_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineExecutionPipelineFragment_solids_definition_configDefinition_type {
  name: string;
  description: string | null;
}

export interface PipelineExecutionPipelineFragment_solids_definition_configDefinition {
  type: PipelineExecutionPipelineFragment_solids_definition_configDefinition_type;
}

export interface PipelineExecutionPipelineFragment_solids_definition {
  metadata: PipelineExecutionPipelineFragment_solids_definition_metadata[];
  configDefinition: PipelineExecutionPipelineFragment_solids_definition_configDefinition | null;
}

export interface PipelineExecutionPipelineFragment_solids_inputs_definition_type {
  name: string;
}

export interface PipelineExecutionPipelineFragment_solids_inputs_definition {
  name: string;
  type: PipelineExecutionPipelineFragment_solids_inputs_definition_type;
}

export interface PipelineExecutionPipelineFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineExecutionPipelineFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineExecutionPipelineFragment_solids_inputs_dependsOn {
  definition: PipelineExecutionPipelineFragment_solids_inputs_dependsOn_definition;
  solid: PipelineExecutionPipelineFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineExecutionPipelineFragment_solids_inputs {
  definition: PipelineExecutionPipelineFragment_solids_inputs_definition;
  dependsOn: PipelineExecutionPipelineFragment_solids_inputs_dependsOn | null;
}

export interface PipelineExecutionPipelineFragment_solids_outputs_definition_type {
  name: string;
}

export interface PipelineExecutionPipelineFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExecutionPipelineFragment_solids_outputs_definition {
  name: string;
  type: PipelineExecutionPipelineFragment_solids_outputs_definition_type;
  expectations: PipelineExecutionPipelineFragment_solids_outputs_definition_expectations[];
}

export interface PipelineExecutionPipelineFragment_solids_outputs_dependedBy_solid {
  name: string;
}

export interface PipelineExecutionPipelineFragment_solids_outputs_dependedBy {
  solid: PipelineExecutionPipelineFragment_solids_outputs_dependedBy_solid;
}

export interface PipelineExecutionPipelineFragment_solids_outputs {
  definition: PipelineExecutionPipelineFragment_solids_outputs_definition;
  dependedBy: PipelineExecutionPipelineFragment_solids_outputs_dependedBy[];
}

export interface PipelineExecutionPipelineFragment_solids {
  name: string;
  definition: PipelineExecutionPipelineFragment_solids_definition;
  inputs: PipelineExecutionPipelineFragment_solids_inputs[];
  outputs: PipelineExecutionPipelineFragment_solids_outputs[];
}

export interface PipelineExecutionPipelineFragment {
  name: string;
  environmentType: PipelineExecutionPipelineFragment_environmentType;
  types: PipelineExecutionPipelineFragment_types[];
  solids: PipelineExecutionPipelineFragment_solids[];
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
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================