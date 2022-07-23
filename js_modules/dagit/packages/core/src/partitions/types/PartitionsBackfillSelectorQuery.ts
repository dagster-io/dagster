/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionsBackfillSelectorQuery
// ====================================================

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions_results[];
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError_causes[];
}

export type PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError = PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_Partitions | PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError_PythonError;

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionsOrError: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionsOrError;
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError";
  message: string;
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionsBackfillSelectorQuery_partitionSetOrError_PythonError_causes[];
}

export type PartitionsBackfillSelectorQuery_partitionSetOrError = PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet | PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionsBackfillSelectorQuery_partitionSetOrError_PythonError;

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
  id: string;
  name: string;
  solidHandles: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError {
  __typename: "PipelineSnapshotNotFoundError";
  message: string;
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PythonError_causes[];
}

export type PartitionsBackfillSelectorQuery_pipelineSnapshotOrError = PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot | PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError | PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshotNotFoundError | PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PythonError;

export interface PartitionsBackfillSelectorQuery_instance_runLauncher {
  __typename: "RunLauncher";
  name: string;
}

export interface PartitionsBackfillSelectorQuery_instance_daemonHealth_daemonStatus {
  __typename: "DaemonStatus";
  id: string;
  healthy: boolean | null;
}

export interface PartitionsBackfillSelectorQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  daemonStatus: PartitionsBackfillSelectorQuery_instance_daemonHealth_daemonStatus;
}

export interface PartitionsBackfillSelectorQuery_instance {
  __typename: "Instance";
  runLauncher: PartitionsBackfillSelectorQuery_instance_runLauncher | null;
  daemonHealth: PartitionsBackfillSelectorQuery_instance_daemonHealth;
  runQueuingSupported: boolean;
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
