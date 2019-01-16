

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineSolidSelectorFragment
// ====================================================

export interface PipelineSolidSelectorFragment_solids_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineSolidSelectorFragment_solids_definition_configDefinition_type {
  name: string;
  description: string | null;
}

export interface PipelineSolidSelectorFragment_solids_definition_configDefinition {
  type: PipelineSolidSelectorFragment_solids_definition_configDefinition_type;
}

export interface PipelineSolidSelectorFragment_solids_definition {
  metadata: PipelineSolidSelectorFragment_solids_definition_metadata[];
  configDefinition: PipelineSolidSelectorFragment_solids_definition_configDefinition | null;
}

export interface PipelineSolidSelectorFragment_solids_inputs_definition_type {
  name: string;
}

export interface PipelineSolidSelectorFragment_solids_inputs_definition {
  name: string;
  type: PipelineSolidSelectorFragment_solids_inputs_definition_type;
}

export interface PipelineSolidSelectorFragment_solids_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineSolidSelectorFragment_solids_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineSolidSelectorFragment_solids_inputs_dependsOn {
  definition: PipelineSolidSelectorFragment_solids_inputs_dependsOn_definition;
  solid: PipelineSolidSelectorFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineSolidSelectorFragment_solids_inputs {
  definition: PipelineSolidSelectorFragment_solids_inputs_definition;
  dependsOn: PipelineSolidSelectorFragment_solids_inputs_dependsOn | null;
}

export interface PipelineSolidSelectorFragment_solids_outputs_definition_type {
  name: string;
}

export interface PipelineSolidSelectorFragment_solids_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineSolidSelectorFragment_solids_outputs_definition {
  name: string;
  type: PipelineSolidSelectorFragment_solids_outputs_definition_type;
  expectations: PipelineSolidSelectorFragment_solids_outputs_definition_expectations[];
}

export interface PipelineSolidSelectorFragment_solids_outputs_dependedBy_solid {
  name: string;
}

export interface PipelineSolidSelectorFragment_solids_outputs_dependedBy {
  solid: PipelineSolidSelectorFragment_solids_outputs_dependedBy_solid;
}

export interface PipelineSolidSelectorFragment_solids_outputs {
  definition: PipelineSolidSelectorFragment_solids_outputs_definition;
  dependedBy: PipelineSolidSelectorFragment_solids_outputs_dependedBy[];
}

export interface PipelineSolidSelectorFragment_solids {
  name: string;
  definition: PipelineSolidSelectorFragment_solids_definition;
  inputs: PipelineSolidSelectorFragment_solids_inputs[];
  outputs: PipelineSolidSelectorFragment_solids_outputs[];
}

export interface PipelineSolidSelectorFragment {
  name: string;
  solids: PipelineSolidSelectorFragment_solids[];
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