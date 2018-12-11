

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphSolidFragment
// ====================================================

export interface PipelineGraphSolidFragment_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineGraphSolidFragment_definition_configDefinition_type {
  description: string | null;
}

export interface PipelineGraphSolidFragment_definition_configDefinition {
  type: PipelineGraphSolidFragment_definition_configDefinition_type;
}

export interface PipelineGraphSolidFragment_definition {
  metadata: PipelineGraphSolidFragment_definition_metadata[];
  configDefinition: PipelineGraphSolidFragment_definition_configDefinition | null;
}

export interface PipelineGraphSolidFragment_inputs_definition_type {
  name: string;
}

export interface PipelineGraphSolidFragment_inputs_definition {
  name: string;
  type: PipelineGraphSolidFragment_inputs_definition_type;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineGraphSolidFragment_inputs_dependsOn {
  definition: PipelineGraphSolidFragment_inputs_dependsOn_definition;
  solid: PipelineGraphSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineGraphSolidFragment_inputs {
  definition: PipelineGraphSolidFragment_inputs_definition;
  dependsOn: PipelineGraphSolidFragment_inputs_dependsOn | null;
}

export interface PipelineGraphSolidFragment_outputs_definition_type {
  name: string;
}

export interface PipelineGraphSolidFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineGraphSolidFragment_outputs_definition {
  name: string;
  type: PipelineGraphSolidFragment_outputs_definition_type;
  expectations: PipelineGraphSolidFragment_outputs_definition_expectations[];
}

export interface PipelineGraphSolidFragment_outputs_dependedBy_solid {
  name: string;
}

export interface PipelineGraphSolidFragment_outputs_dependedBy {
  solid: PipelineGraphSolidFragment_outputs_dependedBy_solid;
}

export interface PipelineGraphSolidFragment_outputs {
  definition: PipelineGraphSolidFragment_outputs_definition;
  dependedBy: PipelineGraphSolidFragment_outputs_dependedBy[] | null;
}

export interface PipelineGraphSolidFragment {
  name: string;
  definition: PipelineGraphSolidFragment_definition;
  inputs: PipelineGraphSolidFragment_inputs[];
  outputs: PipelineGraphSolidFragment_outputs[];
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
  JOIN = "JOIN",
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