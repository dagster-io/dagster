

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeExplorerFragment
// ====================================================

export interface TypeExplorerFragment_RegularType_typeAttributes {
  /**
   * 
   * True if the system defines it and it is the same type across pipelines.
   * Examples include "Int" and "String."
   */
  isBuiltin: boolean;
  /**
   * 
   * Dagster generates types for base elements of the config system (e.g. the solids and
   * context field of the base environment). These types are always present
   * and are typically not relevant to an end user. This flag allows tool authors to
   * filter out those types by default.
   * 
   */
  isSystemConfig: boolean;
  isNamed: boolean;
}

export interface TypeExplorerFragment_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: TypeExplorerFragment_RegularType_typeAttributes;
}

export interface TypeExplorerFragment_CompositeType_typeAttributes {
  /**
   * 
   * True if the system defines it and it is the same type across pipelines.
   * Examples include "Int" and "String."
   */
  isBuiltin: boolean;
  /**
   * 
   * Dagster generates types for base elements of the config system (e.g. the solids and
   * context field of the base environment). These types are always present
   * and are typically not relevant to an end user. This flag allows tool authors to
   * filter out those types by default.
   * 
   */
  isSystemConfig: boolean;
  isNamed: boolean;
}

export interface TypeExplorerFragment_CompositeType_fields_type_typeAttributes {
  isNamed: boolean;
}

export interface TypeExplorerFragment_CompositeType_fields_type {
  name: string;
  description: string | null;
  typeAttributes: TypeExplorerFragment_CompositeType_fields_type_typeAttributes;
}

export interface TypeExplorerFragment_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: TypeExplorerFragment_CompositeType_fields_type;
}

export interface TypeExplorerFragment_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  typeAttributes: TypeExplorerFragment_CompositeType_typeAttributes;
  fields: TypeExplorerFragment_CompositeType_fields[];
}

export type TypeExplorerFragment = TypeExplorerFragment_RegularType | TypeExplorerFragment_CompositeType;

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