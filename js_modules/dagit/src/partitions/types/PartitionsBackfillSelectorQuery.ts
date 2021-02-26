// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineSelector, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionsBackfillSelectorQuery
// ====================================================

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError = PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PythonError | PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError_PartitionStatuses;

export interface PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: PartitionsBackfillSelectorQuery_partitionSetOrError_PartitionSet_partitionStatusesOrError;
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

export interface PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PipelineSnapshotNotFoundError" | "PythonError";
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
  id: string;
  name: string;
  solidHandles: PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export type PartitionsBackfillSelectorQuery_pipelineSnapshotOrError = PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError | PartitionsBackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot;

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
  daemonStatus: PartitionsBackfillSelectorQuery_instance_daemonHealth_daemonStatus;
}

export interface PartitionsBackfillSelectorQuery_instance {
  __typename: "Instance";
  runLauncher: PartitionsBackfillSelectorQuery_instance_runLauncher | null;
  daemonHealth: PartitionsBackfillSelectorQuery_instance_daemonHealth;
  daemonBackfillEnabled: boolean;
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
