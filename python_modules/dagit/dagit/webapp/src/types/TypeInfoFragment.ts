

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeInfoFragment
// ====================================================

export interface TypeInfoFragment_RegularType_innerTypes {
  name: string;
}

export interface TypeInfoFragment_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface TypeInfoFragment_RegularType {
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeInfoFragment_RegularType_innerTypes[];
  description: string | null;
  typeAttributes: TypeInfoFragment_RegularType_typeAttributes;
}

export interface TypeInfoFragment_CompositeType_innerTypes {
  name: string;
}

export interface TypeInfoFragment_CompositeType_fields_type {
  name: string;
}

export interface TypeInfoFragment_CompositeType_fields {
  name: string;
  type: TypeInfoFragment_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeInfoFragment_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeInfoFragment_CompositeType {
  name: string;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeInfoFragment_CompositeType_innerTypes[];
  fields: TypeInfoFragment_CompositeType_fields[];
  description: string | null;
  typeAttributes: TypeInfoFragment_CompositeType_typeAttributes;
}

export type TypeInfoFragment = TypeInfoFragment_RegularType | TypeInfoFragment_CompositeType;

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