/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorPipelinePreset
// ====================================================

export interface ConfigEditorPipelinePreset_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigEditorPipelinePreset {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  tags: ConfigEditorPipelinePreset_tags[];
}
