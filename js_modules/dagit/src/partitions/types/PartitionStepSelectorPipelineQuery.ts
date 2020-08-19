// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineSelector, RepositorySelector, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionStepSelectorPipelineQuery
// ====================================================

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError" | "PipelineNotFoundError" | "PythonError";
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  solid: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid;
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs {
  __typename: "Input";
  dependsOn: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn[];
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid;
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs {
  __typename: "Output";
  dependedBy: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy[];
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid {
  __typename: "Solid";
  name: string;
  definition: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition;
  inputs: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs[];
  outputs: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs[];
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid;
}

export interface PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  name: string;
  solidHandles: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export type PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError = PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError_PipelineSnapshot;

export interface PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
}

export interface PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
}

export interface PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
  runs: PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs[];
}

export interface PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export type PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError | PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions;

export interface PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partitionsOrError: PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet_partitionsOrError;
}

export type PartitionStepSelectorPipelineQuery_partitionSetOrError = PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionStepSelectorPipelineQuery_partitionSetOrError_PartitionSet;

export interface PartitionStepSelectorPipelineQuery {
  pipelineSnapshotOrError: PartitionStepSelectorPipelineQuery_pipelineSnapshotOrError;
  partitionSetOrError: PartitionStepSelectorPipelineQuery_partitionSetOrError;
}

export interface PartitionStepSelectorPipelineQueryVariables {
  pipelineSelector: PipelineSelector;
  repositorySelector: RepositorySelector;
  partitionSetName: string;
}
