

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerContainerQuery_type_RegularType_innerTypes_RegularType_innerTypes[];
  typeAttributes: TypeExplorerContainerQuery_type_RegularType_innerTypes_RegularType_typeAttributes;
}

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_typeAttributes;
  fields: TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType_fields[];
}

export type TypeExplorerContainerQuery_type_RegularType_innerTypes = TypeExplorerContainerQuery_type_RegularType_innerTypes_RegularType | TypeExplorerContainerQuery_type_RegularType_innerTypes_CompositeType;

export interface TypeExplorerContainerQuery_type_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerContainerQuery_type_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerContainerQuery_type_RegularType_innerTypes[];
  typeAttributes: TypeExplorerContainerQuery_type_RegularType_typeAttributes;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_RegularType_innerTypes {
  name: string;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_RegularType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerContainerQuery_type_CompositeType_innerTypes_RegularType_innerTypes[];
  typeAttributes: TypeExplorerContainerQuery_type_CompositeType_innerTypes_RegularType_typeAttributes;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_innerTypes {
  name: string;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_fields_type {
  name: string;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_fields {
  name: string;
  description: string | null;
  type: TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_innerTypes[];
  typeAttributes: TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_typeAttributes;
  fields: TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType_fields[];
}

export type TypeExplorerContainerQuery_type_CompositeType_innerTypes = TypeExplorerContainerQuery_type_CompositeType_innerTypes_RegularType | TypeExplorerContainerQuery_type_CompositeType_innerTypes_CompositeType;

export interface TypeExplorerContainerQuery_type_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerContainerQuery_type_CompositeType_fields_type {
  name: string;
}

export interface TypeExplorerContainerQuery_type_CompositeType_fields {
  name: string;
  description: string | null;
  type: TypeExplorerContainerQuery_type_CompositeType_fields_type;
  isOptional: boolean;
}

export interface TypeExplorerContainerQuery_type_CompositeType {
  name: string;
  description: string | null;
  isDict: boolean;
  isList: boolean;
  isNullable: boolean;
  innerTypes: TypeExplorerContainerQuery_type_CompositeType_innerTypes[];
  typeAttributes: TypeExplorerContainerQuery_type_CompositeType_typeAttributes;
  fields: TypeExplorerContainerQuery_type_CompositeType_fields[];
}

export type TypeExplorerContainerQuery_type = TypeExplorerContainerQuery_type_RegularType | TypeExplorerContainerQuery_type_CompositeType;

export interface TypeExplorerContainerQuery {
  type: TypeExplorerContainerQuery_type | null;
}

export interface TypeExplorerContainerQueryVariables {
  pipelineName: string;
  typeName: string;
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