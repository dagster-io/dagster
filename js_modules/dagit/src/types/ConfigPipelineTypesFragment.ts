

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigPipelineTypesFragment
// ====================================================

export interface ConfigPipelineTypesFragment_types_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigPipelineTypesFragment_types_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: ConfigPipelineTypesFragment_types_RegularType_typeAttributes;
}

export interface ConfigPipelineTypesFragment_types_CompositeType_fields_type {
  __typename: "RegularType" | "CompositeType";
  name: string;
}

export interface ConfigPipelineTypesFragment_types_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigPipelineTypesFragment_types_CompositeType_fields_type;
}

export interface ConfigPipelineTypesFragment_types_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigPipelineTypesFragment_types_CompositeType {
  __typename: "CompositeType";
  fields: ConfigPipelineTypesFragment_types_CompositeType_fields[];
  name: string;
  description: string | null;
  typeAttributes: ConfigPipelineTypesFragment_types_CompositeType_typeAttributes;
}

export type ConfigPipelineTypesFragment_types = ConfigPipelineTypesFragment_types_RegularType | ConfigPipelineTypesFragment_types_CompositeType;

export interface ConfigPipelineTypesFragment {
  types: ConfigPipelineTypesFragment_types[];
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