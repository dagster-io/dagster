// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorGeneratorPipelineFragment
// ====================================================

export interface ConfigEditorGeneratorPipelineFragment_presets_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigEditorGeneratorPipelineFragment_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  tags: ConfigEditorGeneratorPipelineFragment_presets_tags[];
}

export interface ConfigEditorGeneratorPipelineFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigEditorGeneratorPipelineFragment {
  __typename: "Pipeline";
  id: string;
  name: string;
  presets: ConfigEditorGeneratorPipelineFragment_presets[];
  tags: ConfigEditorGeneratorPipelineFragment_tags[];
}
