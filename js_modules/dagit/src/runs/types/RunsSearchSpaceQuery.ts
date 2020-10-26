// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunsSearchSpaceQuery
// ====================================================

export interface RunsSearchSpaceQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface RunsSearchSpaceQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  name: string;
}

export interface RunsSearchSpaceQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  pipelines: RunsSearchSpaceQuery_repositoryOrError_Repository_pipelines[];
}

export type RunsSearchSpaceQuery_repositoryOrError = RunsSearchSpaceQuery_repositoryOrError_PythonError | RunsSearchSpaceQuery_repositoryOrError_Repository;

export interface RunsSearchSpaceQuery_pipelineRunTags {
  __typename: "PipelineTagAndValues";
  key: string;
  values: string[];
}

export interface RunsSearchSpaceQuery {
  repositoryOrError: RunsSearchSpaceQuery_repositoryOrError;
  pipelineRunTags: RunsSearchSpaceQuery_pipelineRunTags[];
}

export interface RunsSearchSpaceQueryVariables {
  repositorySelector: RepositorySelector;
}
