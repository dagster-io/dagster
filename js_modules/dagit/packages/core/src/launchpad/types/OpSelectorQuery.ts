/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: OpSelectorQuery
// ====================================================

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_definition;
  solid: OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn_solid;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs {
  __typename: "Input";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_definition;
  isDynamicCollect: boolean;
  dependsOn: OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs_dependsOn[];
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  displayName: string;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition_type;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_solid;
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy_definition;
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs {
  __typename: "Output";
  definition: OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_definition;
  dependedBy: OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs_dependedBy[];
}

export interface OpSelectorQuery_pipelineOrError_Pipeline_solids {
  __typename: "Solid";
  name: string;
  isDynamicMapped: boolean;
  inputs: OpSelectorQuery_pipelineOrError_Pipeline_solids_inputs[];
  outputs: OpSelectorQuery_pipelineOrError_Pipeline_solids_outputs[];
}

export interface OpSelectorQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  solids: OpSelectorQuery_pipelineOrError_Pipeline_solids[];
}

export interface OpSelectorQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface OpSelectorQuery_pipelineOrError_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export interface OpSelectorQuery_pipelineOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type OpSelectorQuery_pipelineOrError = OpSelectorQuery_pipelineOrError_Pipeline | OpSelectorQuery_pipelineOrError_PipelineNotFoundError | OpSelectorQuery_pipelineOrError_InvalidSubsetError | OpSelectorQuery_pipelineOrError_PythonError;

export interface OpSelectorQuery {
  pipelineOrError: OpSelectorQuery_pipelineOrError;
}

export interface OpSelectorQueryVariables {
  selector: PipelineSelector;
}
