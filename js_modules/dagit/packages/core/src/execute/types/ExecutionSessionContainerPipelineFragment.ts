// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ExecutionSessionContainerPipelineFragment
// ====================================================

export interface ExecutionSessionContainerPipelineFragment_presets_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ExecutionSessionContainerPipelineFragment_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  tags: ExecutionSessionContainerPipelineFragment_presets_tags[];
}

export interface ExecutionSessionContainerPipelineFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ExecutionSessionContainerPipelineFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface ExecutionSessionContainerPipelineFragment {
  __typename: "Pipeline";
  id: string;
  name: string;
  presets: ExecutionSessionContainerPipelineFragment_presets[];
  tags: ExecutionSessionContainerPipelineFragment_tags[];
  modes: ExecutionSessionContainerPipelineFragment_modes[];
}
