

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExplorerSolidFragment
// ====================================================

export interface PipelineExplorerSolidFragment_definition_metadata {
  key: string;
  value: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType {
  description: string | null;
  __typename: "RegularType";
  name: string;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type = PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_RegularType | PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type_CompositeType;

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields_type;
}

export interface PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType {
  description: string | null;
  __typename: "CompositeType";
  name: string;
  fields: PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType_fields[];
}

export type PipelineExplorerSolidFragment_definition_configDefinition_type = PipelineExplorerSolidFragment_definition_configDefinition_type_RegularType | PipelineExplorerSolidFragment_definition_configDefinition_type_CompositeType;

export interface PipelineExplorerSolidFragment_definition_configDefinition {
  type: PipelineExplorerSolidFragment_definition_configDefinition_type;
}

export interface PipelineExplorerSolidFragment_definition {
  metadata: PipelineExplorerSolidFragment_definition_metadata[];
  configDefinition: PipelineExplorerSolidFragment_definition_configDefinition | null;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_inputs_definition {
  name: string;
  type: PipelineExplorerSolidFragment_inputs_definition_type;
  description: string | null;
  expectations: PipelineExplorerSolidFragment_inputs_definition_expectations[];
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_definition {
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn_solid {
  name: string;
}

export interface PipelineExplorerSolidFragment_inputs_dependsOn {
  definition: PipelineExplorerSolidFragment_inputs_dependsOn_definition;
  solid: PipelineExplorerSolidFragment_inputs_dependsOn_solid;
}

export interface PipelineExplorerSolidFragment_inputs {
  definition: PipelineExplorerSolidFragment_inputs_definition;
  dependsOn: PipelineExplorerSolidFragment_inputs_dependsOn | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition_type {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition_expectations {
  name: string;
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_definition {
  name: string;
  type: PipelineExplorerSolidFragment_outputs_definition_type;
  expectations: PipelineExplorerSolidFragment_outputs_definition_expectations[];
  description: string | null;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy_solid {
  name: string;
}

export interface PipelineExplorerSolidFragment_outputs_dependedBy {
  solid: PipelineExplorerSolidFragment_outputs_dependedBy_solid;
}

export interface PipelineExplorerSolidFragment_outputs {
  definition: PipelineExplorerSolidFragment_outputs_definition;
  dependedBy: PipelineExplorerSolidFragment_outputs_dependedBy[] | null;
}

export interface PipelineExplorerSolidFragment {
  name: string;
  definition: PipelineExplorerSolidFragment_definition;
  inputs: PipelineExplorerSolidFragment_inputs[];
  outputs: PipelineExplorerSolidFragment_outputs[];
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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