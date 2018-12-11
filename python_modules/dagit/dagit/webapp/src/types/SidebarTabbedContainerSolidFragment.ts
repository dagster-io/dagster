

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SidebarTabbedContainerSolidFragment
// ====================================================

export interface SidebarTabbedContainerSolidFragment_outputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: SidebarTabbedContainerSolidFragment_outputs_definition_type_typeAttributes;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_outputs_definition {
  name: string;
  type: SidebarTabbedContainerSolidFragment_outputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_outputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_outputs {
  definition: SidebarTabbedContainerSolidFragment_outputs_definition;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_type_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_type {
  name: string;
  description: string | null;
  typeAttributes: SidebarTabbedContainerSolidFragment_inputs_definition_type_typeAttributes;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidFragment_inputs_definition {
  name: string;
  type: SidebarTabbedContainerSolidFragment_inputs_definition_type;
  description: string | null;
  expectations: SidebarTabbedContainerSolidFragment_inputs_definition_expectations[];
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition {
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface SidebarTabbedContainerSolidFragment_inputs_dependsOn {
  definition: SidebarTabbedContainerSolidFragment_inputs_dependsOn_definition;
  solid: SidebarTabbedContainerSolidFragment_inputs_dependsOn_solid;
}

export interface SidebarTabbedContainerSolidFragment_inputs {
  definition: SidebarTabbedContainerSolidFragment_inputs_definition;
  dependsOn: SidebarTabbedContainerSolidFragment_inputs_dependsOn | null;
}

export interface SidebarTabbedContainerSolidFragment_definition_metadata {
  key: string;
  value: string;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_type_typeAttributes {
  isNamed: boolean;
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition_type {
  name: string;
  description: string | null;
  typeAttributes: SidebarTabbedContainerSolidFragment_definition_configDefinition_type_typeAttributes;
  __typename: "RegularType" | "CompositeType";
}

export interface SidebarTabbedContainerSolidFragment_definition_configDefinition {
  type: SidebarTabbedContainerSolidFragment_definition_configDefinition_type;
}

export interface SidebarTabbedContainerSolidFragment_definition {
  description: string | null;
  metadata: SidebarTabbedContainerSolidFragment_definition_metadata[];
  configDefinition: SidebarTabbedContainerSolidFragment_definition_configDefinition | null;
}

export interface SidebarTabbedContainerSolidFragment {
  outputs: SidebarTabbedContainerSolidFragment_outputs[];
  inputs: SidebarTabbedContainerSolidFragment_inputs[];
  name: string;
  definition: SidebarTabbedContainerSolidFragment_definition;
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