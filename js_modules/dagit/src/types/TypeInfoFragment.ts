

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
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeInfoFragment_RegularType_innerTypes[];
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
  description: string | null;
  type: TypeInfoFragment_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeInfoFragment_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeInfoFragment_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeInfoFragment_CompositeType_innerTypes[];
  fields: TypeInfoFragment_CompositeType_fields[];
  typeAttributes: TypeInfoFragment_CompositeType_typeAttributes;
}

export type TypeInfoFragment = TypeInfoFragment_RegularType | TypeInfoFragment_CompositeType;

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
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================