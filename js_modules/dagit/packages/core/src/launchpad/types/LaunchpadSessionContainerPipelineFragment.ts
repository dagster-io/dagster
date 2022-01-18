/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LaunchpadSessionContainerPipelineFragment
// ====================================================

export interface LaunchpadSessionContainerPipelineFragment_presets_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchpadSessionContainerPipelineFragment_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  tags: LaunchpadSessionContainerPipelineFragment_presets_tags[];
}

export interface LaunchpadSessionContainerPipelineFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchpadSessionContainerPipelineFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
}

export interface LaunchpadSessionContainerPipelineFragment {
  __typename: "Pipeline";
  id: string;
  isJob: boolean;
  name: string;
  presets: LaunchpadSessionContainerPipelineFragment_presets[];
  tags: LaunchpadSessionContainerPipelineFragment_tags[];
  modes: LaunchpadSessionContainerPipelineFragment_modes[];
}
