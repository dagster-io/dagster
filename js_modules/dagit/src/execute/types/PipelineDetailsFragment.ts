// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineDetailsFragment
// ====================================================

export interface PipelineDetailsFragment_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
}

export interface PipelineDetailsFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PipelineDetailsFragment {
  __typename: "Pipeline";
  name: string;
  modes: PipelineDetailsFragment_modes[];
  tags: PipelineDetailsFragment_tags[];
}
