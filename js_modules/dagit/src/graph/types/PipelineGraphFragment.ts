

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphFragment
// ====================================================

export interface PipelineGraphFragment_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineGraphFragment_solids_definition_configDefinition_type {
  name: string;
  description: string | null;
}

export interface PipelineGraphFragment_solids_definition_configDefinition {
  type: PipelineGraphFragment_solids_definition_configDefinition_type;
}

export interface PipelineGraphFragment_solids_definition {
  metadata: PipelineGraphFragment_solids_definition_metadata[];
  configDefinition: PipelineGraphFragment_solids_definition_configDefinition | null;
}

export interface PipelineGraphFragment_solids_inputs_definition_type {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_definition {
  name: string;
  type: PipelineGraphFragment_solids_inputs_definition_type;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn {
  definition: PipelineGraphFragment_solids_inputs_dependsOn_definition;
  solid: PipelineGraphFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineGraphFragment_solids_inputs {
  definition: PipelineGraphFragment_solids_inputs_definition;
  dependsOn: PipelineGraphFragment_solids_inputs_dependsOn | null;
}

export interface PipelineGraphFragment_solids_outputs_definition_type {
  name: string;
}

export interface PipelineGraphFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineGraphFragment_solids_outputs_definition {
  name: string;
  type: PipelineGraphFragment_solids_outputs_definition_type;
  expectations: PipelineGraphFragment_solids_outputs_definition_expectations[];
}

export interface PipelineGraphFragment_solids_outputs_dependedBy_solid {
  name: string;
}

export interface PipelineGraphFragment_solids_outputs_dependedBy {
  solid: PipelineGraphFragment_solids_outputs_dependedBy_solid;
}

export interface PipelineGraphFragment_solids_outputs {
  definition: PipelineGraphFragment_solids_outputs_definition;
  dependedBy: PipelineGraphFragment_solids_outputs_dependedBy[];
}

export interface PipelineGraphFragment_solids {
  name: string;
  definition: PipelineGraphFragment_solids_definition;
  inputs: PipelineGraphFragment_solids_inputs[];
  outputs: PipelineGraphFragment_solids_outputs[];
}

export interface PipelineGraphFragment {
  name: string;
  solids: PipelineGraphFragment_solids[];
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