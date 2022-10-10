/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: OverviewSensorsQuery
// ====================================================

export interface OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  description: string | null;
}

export interface OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  sensors: OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors[];
}

export interface OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface OverviewSensorsQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: OverviewSensorsQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface OverviewSensorsQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface OverviewSensorsQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: OverviewSensorsQuery_workspaceOrError_PythonError_causes[];
}

export type OverviewSensorsQuery_workspaceOrError = OverviewSensorsQuery_workspaceOrError_Workspace | OverviewSensorsQuery_workspaceOrError_PythonError;

export interface OverviewSensorsQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
}

export interface OverviewSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
}

export interface OverviewSensorsQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: OverviewSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export type OverviewSensorsQuery_unloadableInstigationStatesOrError = OverviewSensorsQuery_unloadableInstigationStatesOrError_PythonError | OverviewSensorsQuery_unloadableInstigationStatesOrError_InstigationStates;

export interface OverviewSensorsQuery {
  workspaceOrError: OverviewSensorsQuery_workspaceOrError;
  unloadableInstigationStatesOrError: OverviewSensorsQuery_unloadableInstigationStatesOrError;
}
