/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigPresetsQuery
// ====================================================

export interface ConfigPresetsQuery_presetsForPipeline {
  __typename: "PipelinePreset";
  solidSubset: string[] | null;
  name: string;
  environment: string | null;
}

export interface ConfigPresetsQuery {
  presetsForPipeline: ConfigPresetsQuery_presetsForPipeline[] | null;
}

export interface ConfigPresetsQueryVariables {
  pipelineName: string;
}
