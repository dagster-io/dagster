

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigFragment
// ====================================================

export interface ConfigFragment_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface ConfigFragment_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigFragment_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: ConfigFragment_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface ConfigFragment_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface ConfigFragment_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface ConfigFragment_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigFragment_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigFragment_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigFragment_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: ConfigFragment_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: ConfigFragment_type_RegularType_innerTypes_CompositeType_fields[];
}

export type ConfigFragment_type_RegularType_innerTypes = ConfigFragment_type_RegularType_innerTypes_RegularType | ConfigFragment_type_RegularType_innerTypes_CompositeType;

export interface ConfigFragment_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigFragment_type_RegularType_innerTypes[];
  typeAttributes: ConfigFragment_type_RegularType_typeAttributes;
}

export interface ConfigFragment_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface ConfigFragment_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigFragment_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: ConfigFragment_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface ConfigFragment_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface ConfigFragment_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface ConfigFragment_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigFragment_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigFragment_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigFragment_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: ConfigFragment_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: ConfigFragment_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type ConfigFragment_type_CompositeType_innerTypes = ConfigFragment_type_CompositeType_innerTypes_RegularType | ConfigFragment_type_CompositeType_innerTypes_CompositeType;

export interface ConfigFragment_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface ConfigFragment_type_CompositeType_fields_type {
  name: string;
}

export interface ConfigFragment_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: ConfigFragment_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface ConfigFragment_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: ConfigFragment_type_CompositeType_innerTypes[];
  typeAttributes: ConfigFragment_type_CompositeType_typeAttributes;
  fields: ConfigFragment_type_CompositeType_fields[];
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