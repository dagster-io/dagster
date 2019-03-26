/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineSolidSelectorQuery
// ====================================================

export interface PipelineSolidSelectorQuery_pipeline_solids_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_definition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineSolidSelectorQuery_pipeline_solids_definition_configDefinition_configType;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_definition {
  __typename: "SolidDefinition";
  metadata: PipelineSolidSelectorQuery_pipeline_solids_definition_metadata[];
  configDefinition: PipelineSolidSelectorQuery_pipeline_solids_definition_configDefinition | null;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineSolidSelectorQuery_pipeline_solids_inputs_definition_type;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineSolidSelectorQuery_pipeline_solids_inputs_dependsOn_definition;
  solid: PipelineSolidSelectorQuery_pipeline_solids_inputs_dependsOn_solid;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_inputs {
  __typename: "Input";
  definition: PipelineSolidSelectorQuery_pipeline_solids_inputs_definition;
  dependsOn: PipelineSolidSelectorQuery_pipeline_solids_inputs_dependsOn | null;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineSolidSelectorQuery_pipeline_solids_outputs_definition_type;
  expectations: PipelineSolidSelectorQuery_pipeline_solids_outputs_definition_expectations[];
}

export interface PipelineSolidSelectorQuery_pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineSolidSelectorQuery_pipeline_solids_outputs_dependedBy_solid;
}

export interface PipelineSolidSelectorQuery_pipeline_solids_outputs {
  __typename: "Output";
  definition: PipelineSolidSelectorQuery_pipeline_solids_outputs_definition;
  dependedBy: PipelineSolidSelectorQuery_pipeline_solids_outputs_dependedBy[];
}

export interface PipelineSolidSelectorQuery_pipeline_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineSolidSelectorQuery_pipeline_solids_definition;
  inputs: PipelineSolidSelectorQuery_pipeline_solids_inputs[];
  outputs: PipelineSolidSelectorQuery_pipeline_solids_outputs[];
}

export interface PipelineSolidSelectorQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  solids: PipelineSolidSelectorQuery_pipeline_solids[];
}

export interface PipelineSolidSelectorQuery {
  pipeline: PipelineSolidSelectorQuery_pipeline;
}

export interface PipelineSolidSelectorQueryVariables {
  name: string;
}
