

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidTypeSignatureFragment
// ====================================================

export interface SolidTypeSignatureFragment_outputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface SolidTypeSignatureFragment_outputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: SolidTypeSignatureFragment_outputs_definition_type_typeAttributes;
}

export interface SolidTypeSignatureFragment_outputs_definition {
  name: string;
  type: SolidTypeSignatureFragment_outputs_definition_type;
}

export interface SolidTypeSignatureFragment_outputs {
  definition: SolidTypeSignatureFragment_outputs_definition;
}

export interface SolidTypeSignatureFragment_inputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface SolidTypeSignatureFragment_inputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: SolidTypeSignatureFragment_inputs_definition_type_typeAttributes;
}

export interface SolidTypeSignatureFragment_inputs_definition {
  name: string;
  type: SolidTypeSignatureFragment_inputs_definition_type;
}

export interface SolidTypeSignatureFragment_inputs {
  definition: SolidTypeSignatureFragment_inputs_definition;
}

export interface SolidTypeSignatureFragment {
  outputs: SolidTypeSignatureFragment_outputs[];
  inputs: SolidTypeSignatureFragment_inputs[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
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