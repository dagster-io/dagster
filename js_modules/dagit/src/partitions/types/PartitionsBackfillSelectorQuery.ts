// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineSelector, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionsBackfillSelectorQuery
// ====================================================

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
  runs: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results_runs[];
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_cause | null;
}

export type PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions | PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError;

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  partitionsOrError: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError;
  name: string;
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError";
  message: string;
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type PartitionsBackfillSelectorQuery_partitionSetOrError = PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet | PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionsBackfillSelectorQuery_partitionSetOrError_PythonError;

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError" | "PipelineNotFoundError" | "PythonError";
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  solid: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs {
  __typename: "Input";
  dependsOn: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn[];
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs {
  __typename: "Output";
  dependedBy: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy[];
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid {
  __typename: "Solid";
  name: string;
  definition: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition;
  inputs: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs[];
  outputs: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs[];
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  name: string;
  solidHandles: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export type PartitionsBackfillSelectorQuery_pipelineSnapshotOrError = PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot;

export interface PartitionsBackfillSelectorQuery_instance_runLauncher {
  __typename: "RunLauncher";
  name: string;
}

export interface PartitionsBackfillSelectorQuery_instance {
  __typename: "Instance";
  runLauncher: PartitionsBackfillSelectorQuery_instance_runLauncher | null;
}

export interface PartitionsBackfillSelectorQuery {
  partitionSetOrError: PartitionsBackfillSelectorQuery_partitionSetOrError;
  pipelineSnapshotOrError: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError;
  instance: PartitionsBackfillSelectorQuery_instance;
}

export interface PartitionsBackfillSelectorQueryVariables {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
  pipelineSelector: PipelineSelector;
}
