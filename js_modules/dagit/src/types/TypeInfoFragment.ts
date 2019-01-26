

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeInfoFragment
// ====================================================

export interface TypeInfoFragment_EnumConfigType_innerTypes {
  key: string;
}

export interface TypeInfoFragment_EnumConfigType {
  key: string;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeInfoFragment_EnumConfigType_innerTypes[];
  name: string | null;
}

export interface TypeInfoFragment_CompositeConfigType_innerTypes {
  key: string;
}

export interface TypeInfoFragment_CompositeConfigType_fields_configType {
  key: string;
}

export interface TypeInfoFragment_CompositeConfigType_fields {
  name: string;
  description: string | null;
  configType: TypeInfoFragment_CompositeConfigType_fields_configType;
  isOptional: boolean;
}

export interface TypeInfoFragment_CompositeConfigType {
  key: string;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeInfoFragment_CompositeConfigType_innerTypes[];
  fields: TypeInfoFragment_CompositeConfigType_fields[];
  name: string | null;
}

export type TypeInfoFragment = TypeInfoFragment_EnumConfigType | TypeInfoFragment_CompositeConfigType;

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