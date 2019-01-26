

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_runtimeTypeOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "RuntimeTypeNotFoundError";
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_innerTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields_configType {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields_configType;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_innerTypes[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_innerTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields_configType {
  key: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields_configType;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType {
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_innerTypes[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType {
  __typename: "RegularRuntimeType";
  name: string | null;
  description: string | null;
  inputSchemaType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType | null;
  outputSchemaType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType | null;
}

export type TypeExplorerContainerQuery_runtimeTypeOrError = TypeExplorerContainerQuery_runtimeTypeOrError_PipelineNotFoundError | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType;

export interface TypeExplorerContainerQuery {
  runtimeTypeOrError: TypeExplorerContainerQuery_runtimeTypeOrError | null;
}

export interface TypeExplorerContainerQueryVariables {
  pipelineName: string;
  runtimeTypeName: string;
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