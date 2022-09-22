/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: WorkspaceSensorsQuery
// ====================================================

export interface WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  description: string | null;
}

export interface WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  sensors: WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors[];
}

export interface WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_causes[];
}

export type WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  locationOrLoadError: WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface WorkspaceSensorsQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: WorkspaceSensorsQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface WorkspaceSensorsQuery_workspaceOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface WorkspaceSensorsQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: WorkspaceSensorsQuery_workspaceOrError_PythonError_causes[];
}

export type WorkspaceSensorsQuery_workspaceOrError = WorkspaceSensorsQuery_workspaceOrError_Workspace | WorkspaceSensorsQuery_workspaceOrError_PythonError;

export interface WorkspaceSensorsQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
}

export interface WorkspaceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
}

export interface WorkspaceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: WorkspaceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export type WorkspaceSensorsQuery_unloadableInstigationStatesOrError = WorkspaceSensorsQuery_unloadableInstigationStatesOrError_PythonError | WorkspaceSensorsQuery_unloadableInstigationStatesOrError_InstigationStates;

export interface WorkspaceSensorsQuery {
  workspaceOrError: WorkspaceSensorsQuery_workspaceOrError;
  unloadableInstigationStatesOrError: WorkspaceSensorsQuery_unloadableInstigationStatesOrError;
}
