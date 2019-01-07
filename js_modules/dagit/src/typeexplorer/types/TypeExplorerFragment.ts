

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeExplorerFragment
// ====================================================

export interface TypeExplorerFragment_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface TypeExplorerFragment_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerFragment_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerFragment_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: TypeExplorerFragment_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface TypeExplorerFragment_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface TypeExplorerFragment_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerFragment_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface TypeExplorerFragment_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: TypeExplorerFragment_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeExplorerFragment_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerFragment_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: TypeExplorerFragment_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: TypeExplorerFragment_RegularType_innerTypes_CompositeType_fields[];
}

export type TypeExplorerFragment_RegularType_innerTypes = TypeExplorerFragment_RegularType_innerTypes_RegularType | TypeExplorerFragment_RegularType_innerTypes_CompositeType;

export interface TypeExplorerFragment_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerFragment_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerFragment_RegularType_innerTypes[];
  typeAttributes: TypeExplorerFragment_RegularType_typeAttributes;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerFragment_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: TypeExplorerFragment_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: TypeExplorerFragment_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeExplorerFragment_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerFragment_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: TypeExplorerFragment_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: TypeExplorerFragment_CompositeType_innerTypes_CompositeType_fields[];
}

export type TypeExplorerFragment_CompositeType_innerTypes = TypeExplorerFragment_CompositeType_innerTypes_RegularType | TypeExplorerFragment_CompositeType_innerTypes_CompositeType;

export interface TypeExplorerFragment_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerFragment_CompositeType_fields_type {
  name: string;
}

export interface TypeExplorerFragment_CompositeType_fields {
  name: string;
  description: string | null;
  type: TypeExplorerFragment_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeExplorerFragment_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerFragment_CompositeType_innerTypes[];
  typeAttributes: TypeExplorerFragment_CompositeType_typeAttributes;
  fields: TypeExplorerFragment_CompositeType_fields[];
}

export type TypeExplorerFragment = TypeExplorerFragment_RegularType | TypeExplorerFragment_CompositeType;

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