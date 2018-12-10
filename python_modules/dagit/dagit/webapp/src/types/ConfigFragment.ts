

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigFragment
// ====================================================

export interface ConfigFragment_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: ConfigFragment_type_RegularType_typeAttributes;
}

export interface ConfigFragment_type_CompositeType_fields_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
  typeAttributes: ConfigFragment_type_CompositeType_fields_type_RegularType_typeAttributes;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType_fields_type_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
  typeAttributes: ConfigFragment_type_CompositeType_fields_type_CompositeType_fields_type_typeAttributes;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigFragment_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  typeAttributes: ConfigFragment_type_CompositeType_fields_type_CompositeType_typeAttributes;
  fields: ConfigFragment_type_CompositeType_fields_type_CompositeType_fields[];
}

export type ConfigFragment_type_CompositeType_fields_type = ConfigFragment_type_CompositeType_fields_type_RegularType | ConfigFragment_type_CompositeType_fields_type_CompositeType;

export interface ConfigFragment_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigFragment_type_CompositeType_fields_type;
}

export interface ConfigFragment_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: ConfigFragment_type_CompositeType_fields[];
  typeAttributes: ConfigFragment_type_CompositeType_typeAttributes;
}

export type ConfigFragment_type = ConfigFragment_type_RegularType | ConfigFragment_type_CompositeType;

export interface ConfigFragment {
  type: ConfigFragment_type;
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