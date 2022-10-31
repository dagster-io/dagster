/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RunsSearchSpaceQuery
// ====================================================

export interface RunsSearchSpaceQuery_pipelineRunTags {
  __typename: "PipelineTagAndValues";
  key: string;
  values: string[];
}

export interface RunsSearchSpaceQuery {
  pipelineRunTags: RunsSearchSpaceQuery_pipelineRunTags[];
}
