/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LaunchpadSessionPipelineFragment
// ====================================================

export interface LaunchpadSessionPipelineFragment_presets_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchpadSessionPipelineFragment_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
  tags: LaunchpadSessionPipelineFragment_presets_tags[];
}

export interface LaunchpadSessionPipelineFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface LaunchpadSessionPipelineFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
  description: string | null;
}

export interface LaunchpadSessionPipelineFragment {
  __typename: "Pipeline";
  id: string;
  isJob: boolean;
  name: string;
  presets: LaunchpadSessionPipelineFragment_presets[];
  tags: LaunchpadSessionPipelineFragment_tags[];
  modes: LaunchpadSessionPipelineFragment_modes[];
}
