// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionRunMatrixPipelineQuery
// ====================================================

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PipelineSnapshotNotFoundError" | "PythonError";
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  solid: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid;
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs {
  __typename: "Input";
  dependsOn: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn[];
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid;
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs {
  __typename: "Output";
  dependedBy: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy[];
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid {
  __typename: "Solid";
  name: string;
  definition: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition;
  inputs: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs[];
  outputs: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs[];
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid;
}

export interface PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  solidHandles: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export type PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError = PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineNotFoundError | PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot;

export interface PartitionRunMatrixPipelineQuery {
  pipelineSnapshotOrError: PartitionRunMatrixPipelineQuery_pipelineSnapshotOrError;
}

export interface PartitionRunMatrixPipelineQueryVariables {
  pipelineSelector?: PipelineSelector | null;
}
