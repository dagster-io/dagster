/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphFragment
// ====================================================

export interface PipelineGraphFragment_solids_definition_metadata {
  __typename: "SolidMetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphFragment_solids_definition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineGraphFragment_solids_definition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineGraphFragment_solids_definition_configDefinition_configType;
}

export interface PipelineGraphFragment_solids_definition {
  __typename: "SolidDefinition";
  metadata: PipelineGraphFragment_solids_definition_metadata[];
  configDefinition: PipelineGraphFragment_solids_definition_configDefinition | null;
}

export interface PipelineGraphFragment_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineGraphFragment_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_inputs_definition_type;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_inputs_dependsOn_definition_type;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineGraphFragment_solids_inputs_dependsOn_definition;
  solid: PipelineGraphFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineGraphFragment_solids_inputs {
  __typename: "Input";
  definition: PipelineGraphFragment_solids_inputs_definition;
  dependsOn: PipelineGraphFragment_solids_inputs_dependsOn | null;
}

export interface PipelineGraphFragment_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineGraphFragment_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineGraphFragment_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_outputs_definition_type;
  expectations: PipelineGraphFragment_solids_outputs_definition_expectations[];
}

export interface PipelineGraphFragment_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphFragment_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface PipelineGraphFragment_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_outputs_dependedBy_definition_type;
}

export interface PipelineGraphFragment_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineGraphFragment_solids_outputs_dependedBy_solid;
  definition: PipelineGraphFragment_solids_outputs_dependedBy_definition;
}

export interface PipelineGraphFragment_solids_outputs {
  __typename: "Output";
  definition: PipelineGraphFragment_solids_outputs_definition;
  dependedBy: PipelineGraphFragment_solids_outputs_dependedBy[];
}

export interface PipelineGraphFragment_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineGraphFragment_solids_definition;
  inputs: PipelineGraphFragment_solids_inputs[];
  outputs: PipelineGraphFragment_solids_outputs[];
}

export interface PipelineGraphFragment {
  __typename: "Pipeline";
  name: string;
  solids: PipelineGraphFragment_solids[];
}
