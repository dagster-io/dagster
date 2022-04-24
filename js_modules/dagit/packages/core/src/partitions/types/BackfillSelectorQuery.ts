/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: BackfillSelectorQuery
// ====================================================

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "PipelineSnapshotNotFoundError" | "PythonError";
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn {
  __typename: "Output";
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn_solid;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs {
  __typename: "Input";
  dependsOn: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs_dependsOn[];
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy {
  __typename: "Input";
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy_solid;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs {
  __typename: "Output";
  dependedBy: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs_dependedBy[];
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid {
  __typename: "Solid";
  name: string;
  definition: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_definition;
  inputs: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_inputs[];
  outputs: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid_outputs[];
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles {
  __typename: "SolidHandle";
  handleID: string;
  solid: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles_solid;
}

export interface BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  id: string;
  name: string;
  solidHandles: BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot_solidHandles[];
}

export type BackfillSelectorQuery_pipelineSnapshotOrError = BackfillSelectorQuery_pipelineSnapshotOrError_PipelineNotFoundError | BackfillSelectorQuery_pipelineSnapshotOrError_PipelineSnapshot;

export interface BackfillSelectorQuery_instance_runLauncher {
  __typename: "RunLauncher";
  name: string;
}

export interface BackfillSelectorQuery_instance_daemonHealth_daemonStatus {
  __typename: "DaemonStatus";
  id: string;
  healthy: boolean | null;
}

export interface BackfillSelectorQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  daemonStatus: BackfillSelectorQuery_instance_daemonHealth_daemonStatus;
}

export interface BackfillSelectorQuery_instance {
  __typename: "Instance";
  runLauncher: BackfillSelectorQuery_instance_runLauncher | null;
  daemonHealth: BackfillSelectorQuery_instance_daemonHealth;
  runQueuingSupported: boolean;
}

export interface BackfillSelectorQuery {
  pipelineSnapshotOrError: BackfillSelectorQuery_pipelineSnapshotOrError;
  instance: BackfillSelectorQuery_instance;
}

export interface BackfillSelectorQueryVariables {
  pipelineSelector: PipelineSelector;
}
