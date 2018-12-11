

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarSolidInfoPipelineFragment
// ====================================================

export interface SidebarSolidInfoPipelineFragment_types_RegularType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoPipelineFragment_types_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: SidebarSolidInfoPipelineFragment_types_RegularType_typeAttributes;
}

export interface SidebarSolidInfoPipelineFragment_types_CompositeType_fields_type {
  __typename: "RegularType" | "CompositeType";
  name: string;
}

export interface SidebarSolidInfoPipelineFragment_types_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: SidebarSolidInfoPipelineFragment_types_CompositeType_fields_type;
}

export interface SidebarSolidInfoPipelineFragment_types_CompositeType_typeAttributes {
  isNamed: boolean;
}

export interface SidebarSolidInfoPipelineFragment_types_CompositeType {
  __typename: "CompositeType";
  fields: SidebarSolidInfoPipelineFragment_types_CompositeType_fields[];
  name: string;
  description: string | null;
  typeAttributes: SidebarSolidInfoPipelineFragment_types_CompositeType_typeAttributes;
}

export type SidebarSolidInfoPipelineFragment_types = SidebarSolidInfoPipelineFragment_types_RegularType | SidebarSolidInfoPipelineFragment_types_CompositeType;

export interface SidebarSolidInfoPipelineFragment {
  types: SidebarSolidInfoPipelineFragment_types[];
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