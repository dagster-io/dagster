/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: GraphExplorerSolidHandleFragment
// ====================================================

export interface GraphExplorerSolidHandleFragment_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerSolidHandleFragment_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: GraphExplorerSolidHandleFragment_solid_inputs_dependsOn_definition_type;
}

export interface GraphExplorerSolidHandleFragment_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_inputs_dependsOn {
  __typename: "Output";
  definition: GraphExplorerSolidHandleFragment_solid_inputs_dependsOn_definition;
  solid: GraphExplorerSolidHandleFragment_solid_inputs_dependsOn_solid;
}

export interface GraphExplorerSolidHandleFragment_solid_inputs {
  __typename: "Input";
  definition: GraphExplorerSolidHandleFragment_solid_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: GraphExplorerSolidHandleFragment_solid_inputs_dependsOn[];
}

export interface GraphExplorerSolidHandleFragment_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerSolidHandleFragment_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerSolidHandleFragment_solid_outputs_dependedBy_definition_type;
}

export interface GraphExplorerSolidHandleFragment_solid_outputs_dependedBy {
  __typename: "Input";
  solid: GraphExplorerSolidHandleFragment_solid_outputs_dependedBy_solid;
  definition: GraphExplorerSolidHandleFragment_solid_outputs_dependedBy_definition;
}

export interface GraphExplorerSolidHandleFragment_solid_outputs {
  __typename: "Output";
  definition: GraphExplorerSolidHandleFragment_solid_outputs_definition;
  dependedBy: GraphExplorerSolidHandleFragment_solid_outputs_dependedBy[];
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions_type;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions_type;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
  description: string | null;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField_configType;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  name: string;
  description: string | null;
  metadata: GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_metadata[];
  inputDefinitions: GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_inputDefinitions[];
  outputDefinitions: GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_outputDefinitions[];
  configField: GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition_configField | null;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  isDynamic: boolean | null;
  type: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  name: string;
  description: string | null;
  metadata: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_metadata[];
  inputDefinitions: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  outputDefinitions: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  id: string;
  inputMappings: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type GraphExplorerSolidHandleFragment_solid_definition = GraphExplorerSolidHandleFragment_solid_definition_SolidDefinition | GraphExplorerSolidHandleFragment_solid_definition_CompositeSolidDefinition;

export interface GraphExplorerSolidHandleFragment_solid {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: GraphExplorerSolidHandleFragment_solid_inputs[];
  outputs: GraphExplorerSolidHandleFragment_solid_outputs[];
  definition: GraphExplorerSolidHandleFragment_solid_definition;
}

export interface GraphExplorerSolidHandleFragment {
  __typename: "SolidHandle";
  handleID: string;
  solid: GraphExplorerSolidHandleFragment_solid;
}
